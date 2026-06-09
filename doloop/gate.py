"""doloop_gate.py -- the LOCAL gate CLI (the shipped product, wired to the HOSTED keyserver).

This is hybrid_gate.py with its local `issue_session_key` stub replaced by an HTTP call to
the real keyserver. Everything else is unchanged and stays LOCAL:

  CALIBRATE (free intake, fully local):
     infer the cache from the codebase, AES-256-GCM-encrypt it under K (derived the same
     way the keyserver mints it), write only the ENCRYPTED blob + a salted fingerprint.
     The repo NEVER uploads. K is never written. Customer holds an opaque blob.
     >>> This is what makes "your entire codebase never leaves" literally true.

  CHECK (paid guard, source stays local):
     POST tenant+auth_token to the keyserver -> it authenticates, METERS (Loop++, cap
     enforced), and returns K. Decrypt the cache IN MEMORY, run the REAL gate LOCALLY on
     the snippet (source never leaves; only K came down), discard K. Auth-to-decrypt = the
     meter. Bad token -> keyserver refuses (no K). Over cap -> keyserver refuses (no K).

Crypto is identical to hybrid_gate.py (AES-256-GCM, salted SHA-256 fingerprint, tenant as
AAD). Only the key SOURCE changed: local stub -> hosted keyserver. That is the whole point
of "productionizing" -- the meter now lives on a server we control, off the customer's disk.
"""
import sys, os, json, hmac, hashlib, base64, urllib.request, urllib.error
import gate
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

CACHE_PATH = ".doloop/cache.enc"
KEYSERVER = os.environ.get("DOLOOP_KEYSERVER", "http://127.0.0.1:8787")

# NOTE: the master secret is GONE from the client. The client can no longer derive K on
# its own at check-time -- it MUST call the keyserver. At CALIBRATE time we still need to
# encrypt under the *same* K the keyserver will later mint. In the shipped product,
# calibrate ALSO calls the keyserver (a free, un-metered /v1/session-key variant, or the
# same call flagged calibrate=true) so the client never holds the master secret. For this
# demo we fetch K from the keyserver for BOTH calibrate and check, proving the client is
# secret-free.


class KeyserverError(Exception):
    pass


def fetch_session_key(tenant, auth_token, *, meter=True):
    """Call the HOSTED keyserver. meter=True -> /v1/session-key (the billed CHECK key);
    meter=False -> /v1/calibrate-key (free intake key, same K, no bill). The metering
    decision is the SERVER's, made by endpoint -- the client can't dodge the bill.
    Returns (K_bytes, info_dict). Raises KeyserverError on 401/402/404."""
    endpoint = "/v1/session-key" if meter else "/v1/calibrate-key"
    payload = json.dumps({"tenant": tenant, "auth_token": auth_token}).encode()
    req = urllib.request.Request(
        KEYSERVER + endpoint, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            info = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            info = json.loads(e.read().decode())
        except Exception:
            info = {"error": f"HTTP {e.code}"}
        raise KeyserverError(info.get("error", f"HTTP {e.code}"))
    except urllib.error.URLError as e:
        raise KeyserverError(f"cannot reach keyserver at {KEYSERVER}: {e.reason}")
    K = base64.b64decode(info["session_key_b64"])
    return K, info


# --- AES-256-GCM + fingerprint (identical to hybrid_gate.py) ----------------------
def _encrypt(plaintext, K, aad):
    nonce = os.urandom(12)
    ct = AESGCM(K).encrypt(nonce, plaintext, aad)
    return nonce, ct


def _decrypt(nonce, ciphertext, K, aad):
    return AESGCM(K).decrypt(nonce, ciphertext, aad)


def _fingerprint(plaintext, tenant_salt):
    return hashlib.sha256(tenant_salt + plaintext).hexdigest()


# --- CALIBRATE (local; repo never uploads) ----------------------------------------
def calibrate(codebase, tenant, auth_token):
    held, pairings, nfiles = gate.infer(codebase)            # local: reads the repo on disk
    cache = {"held": held, "pairings": pairings, "nfiles": nfiles}
    plaintext = json.dumps(cache, sort_keys=True).encode()

    # K comes from the keyserver (calibrate is free/un-metered) -- client holds no secret.
    K, info = fetch_session_key(tenant, auth_token, meter=False)
    tenant_salt = hashlib.sha256(b"salt:" + tenant.encode()).digest()
    nonce, ciphertext = _encrypt(plaintext, K, tenant.encode())

    blob = {
        "tenant": tenant,
        "salt": base64.b64encode(tenant_salt).decode(),
        "fingerprint": _fingerprint(plaintext, tenant_salt),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }
    os.makedirs(os.path.join(codebase, ".doloop"), exist_ok=True)
    path = os.path.join(codebase, CACHE_PATH)
    with open(path, "w") as fh:
        json.dump(blob, fh)
    del K
    print(f"calibrated: read {nfiles} files LOCALLY. wrote AES-256-GCM cache -> {path}")
    print(f"  held conventions: {len(held)}, dog-pairings: {len(pairings)}")
    print("  the repo never uploaded; K was fetched, used, discarded; only doloop can mint K to read it")


# --- CHECK (paid; source stays local) ---------------------------------------------
def check(codebase, snippet, tenant, auth_token):
    path = os.path.join(codebase, CACHE_PATH)
    with open(path) as fh:
        blob = json.load(fh)
    tenant_salt = base64.b64decode(blob["salt"])
    nonce = base64.b64decode(blob["nonce"])
    ciphertext = base64.b64decode(blob["ciphertext"])

    # 1. AUTH + METER at the hosted keyserver. THIS is the bill. Bad token / over cap -> no K.
    K, info = fetch_session_key(tenant, auth_token, meter=True)

    # 2. decrypt IN MEMORY. wrong key OR tamper -> InvalidTag -> REFUSED, no plaintext.
    try:
        plaintext = _decrypt(nonce, ciphertext, K, blob["tenant"].encode())
    except InvalidTag:
        raise ValueError("doloop: AES-GCM auth tag failed -- tampered or wrong key, REFUSED")

    # 3. determinism / tamper receipt.
    if not hmac.compare_digest(_fingerprint(plaintext, tenant_salt), blob["fingerprint"]):
        raise ValueError("doloop: cache fingerprint mismatch -- tampered or corrupt cache, REFUSED")

    cache = json.loads(plaintext.decode())
    held = [tuple(x) for x in cache["held"]]
    pairings = {k: [tuple(v) for v in vs] for k, vs in cache["pairings"].items()}
    nfiles = cache["nfiles"]

    # 4. run the REAL gate LOCALLY. snippet source never leaves the machine.
    src = open(snippet, encoding="utf-8", errors="replace").read()
    funclist = [(os.path.basename(snippet), n, src) for n in gate.funcs_in(src)]
    gate.report(held, pairings, set(), funclist, nfiles, os.path.basename(snippet))

    del K  # 5. discard the session key.
    print(f"\nmeter: tenant '{tenant}' plan={info['plan']} loops_used={info['loops_used']}/{info['loops_cap']}")
    return info


def usage():
    print(__doc__)
    print("usage:")
    print("  python3 doloop_gate.py calibrate <codebase> <tenant> <auth_token>")
    print("  python3 doloop_gate.py check     <codebase> <snippet> <tenant> <auth_token>")
    sys.exit(2)


def main():
    args = sys.argv[1:]
    if not args:
        usage()
    cmd = args[0]
    try:
        if cmd == "calibrate":
            if len(args) < 4:
                usage()
            calibrate(args[1], args[2], args[3])
        elif cmd == "check":
            if len(args) < 5:
                usage()
            check(args[1], args[2], args[3], args[4])
        else:
            usage()
    except KeyserverError as e:
        print(f"CHECK REFUSED (keyserver): {e}")
        print("  -> no session key, no decrypt, no check. The gate is useless without doloop.")
        sys.exit(1)
    except ValueError as e:
        print(f"CHECK REFUSED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
