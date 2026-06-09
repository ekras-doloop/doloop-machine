#!/usr/bin/env python3
"""
doloop — the resistance machine, from the CLI.

A thin client: it sends your AI's output to the doloop machine and gets back a
deterministic verdict (same input, same verdict, every time). The donkey rules
stay server-side; this client never holds them. Bring your own key.

Install:  pip install doloopio
Auth:     export DOLOOP_KEY=dlp_...        (get one at https://api.doloop.io/dashboard)
Usage:
  doloop loops                              # loops remaining on your key
  doloop check "the answer your model produced"
  doloop check -f answer.txt                # check a file
  echo "..." | doloop check                 # check stdin
  doloop check --donkey conversations "User: ...\nBot: ..."
  doloop design https://example.com         # design review of a live URL
  doloop code file.c [more.py ...]          # gate code, exit 1 on a fail (for CI)
  doloop gate calibrate <dir> <tenant> <key>  # local gate: encrypt the codebase cache (free)
  doloop gate check <dir> <file> <tenant> <key> # local gate: phone home to meter+mint a key, check locally, source never leaves
"""
import sys, os, json, re, subprocess, urllib.request, urllib.error

API = os.environ.get("DOLOOP_API", "https://api.doloop.io")
KEY = os.environ.get("DOLOOP_KEY", "")


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("content-type", "application/json")
    if KEY:
        r.add_header("Authorization", "Bearer " + KEY)
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}"), dict(e.headers)
        except Exception:
            return e.code, {}, {}
    except Exception as e:
        return 0, {"error": str(e)}, {}


def _text(args):
    if "-f" in args:
        return open(args[args.index("-f") + 1], encoding="utf-8").read()
    pos = [a for i, a in enumerate(args)
           if not a.startswith("-") and (i == 0 or args[i - 1] not in ("-f", "--donkey"))]
    if pos:
        return pos[-1]
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def cmd_check(args):
    donkey = args[args.index("--donkey") + 1] if "--donkey" in args else "writing"
    text = _text(args)
    if not text:
        sys.exit("nothing to check. pass text, -f file, or pipe stdin.")
    st, body, hdr = req("POST", "/v1/check", {"text": text, "donkey": donkey})
    print(json.dumps(body, indent=2))
    rem = hdr.get("x-doloop-loops-remaining") or hdr.get("X-Doloop-Loops-Remaining")
    if rem:
        print("loops remaining: " + rem, file=sys.stderr)
    sys.exit(0 if body.get("verdict") == "pass" else 2)


def cmd_design(args):
    url = next((a for a in args if a.startswith("http")), None)
    if not url:
        sys.exit("usage: doloop design https://your-url")
    st, body, _ = req("POST", "/v1/check-design", {"url": url})
    if st == 404:
        sys.exit("the design endpoint is not live yet on this machine.")
    print(json.dumps(body, indent=2))
    sys.exit(0 if body.get("verdict") == "pass" else 2)


def _changed_lines(path, base):
    """Added/changed line numbers in path between base and the working tree (via git diff)."""
    try:
        out = subprocess.run(["git", "diff", "--unified=0", base, "--", path],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    changed = set()
    for line in out.splitlines():
        m = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
        if m:
            start = int(m.group(1))
            count = int(m.group(2) or "1")
            changed.update(range(start, start + max(count, 1)))
    return changed


def cmd_code(args):
    """Gate source files. With --diff <ref>, only findings on changed lines gate. Exits 1 on a fail."""
    base = None
    rest = list(args)
    if "--diff" in rest:
        i = rest.index("--diff")
        base = rest[i + 1] if i + 1 < len(rest) else "HEAD~1"
        del rest[i:i + 2]
    files = [a for a in rest if not a.startswith("-")]
    if not files:
        sys.exit("usage: doloop code [--diff <ref>] <file> [file ...]")
    any_fail = False
    for path in files:
        try:
            code = open(path, encoding="utf-8", errors="replace").read()
        except Exception as e:
            print(f"{path}: cannot read ({e})", file=sys.stderr)
            continue
        st, body, _ = req("POST", "/v1/check-code", {"code": code, "language": "auto"})
        if st == 404:
            sys.exit("the code endpoint is not live on this machine.")
        findings = body.get("findings", [])
        if base is not None:
            changed = _changed_lines(path, base)
            if changed is not None:
                findings = [f for f in findings if f.get("line") in changed]
        v = "fail" if any(f.get("severity") == "fail" for f in findings) else "pass"
        mark = "FAIL" if v == "fail" else ("WARN" if findings else "PASS")
        print(f"{path}: {mark} ({len(findings)} findings){' (diff)' if base else ''}")
        for f in findings:
            cwe = (" " + f["cwe"]) if f.get("cwe") else ""
            print(f"  [{f.get('severity', '').upper()}] {f.get('check')}{cwe} L{f.get('line')}: {f.get('message')}")
        if v == "fail":
            any_fail = True
    sys.exit(1 if any_fail else 0)


def cmd_loops(args):
    if not KEY:
        sys.exit("set DOLOOP_KEY=dlp_... (get one at https://api.doloop.io/dashboard)")
    st, body, _ = req("GET", "/v1/balance")
    if st == 401:
        sys.exit("key not recognized. check DOLOOP_KEY.")
    n = body.get("loops_remaining")
    print(f"{n:,} loops remaining" if isinstance(n, int) else json.dumps(body))


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"
    rest = args[1:]
    if cmd == "check":
        cmd_check(rest)
    elif cmd == "design":
        cmd_design(rest)
    elif cmd == "code":
        cmd_code(rest)
    elif cmd == "gate":
        from . import gate as _gate
        sys.argv = ["doloop-gate"] + rest
        _gate.main()
    elif cmd in ("loops", "balance"):
        cmd_loops(rest)
    else:
        print(__doc__.strip())


if __name__ == "__main__":
    main()
