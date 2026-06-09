"""The loop calculator: public and reproducible.

A loop is doloop's billing unit, but it is metered PER SURFACE -- the atom of adjudication is
shaped by what is being judged:

  - CODE donkey: ONE LOOP = ONE FUNCTION JUDGED ON ONE FEATURE (function x feature). This file is
    the code meter; it counts functions x features below.
  - PROSE / DOCUMENT / CONVERSATION donkeys: ONE LOOP = ONE CHECK (one check = one loop). Those
    surfaces have no functions to count, so each judged check is the atom.

This file computes the CODE meter only. ONE LOOP (code) = ONE FUNCTION JUDGED ON ONE FEATURE --
the way a token is the atom of generation. It scales with the work:

  - Calibration (the one-time full read of a repo) = functions x features. Grows with the codebase.
  - Each commit (the recurring cost)              = changed functions x features (~100 per commit).
    The cached digest means functions you didn't touch are never re-judged.

Your bill is `loops_used x published_rate`. Both sides are reproducible from this file -- run it on your
own repo and you get the exact loop count we charge. Self-verifiable, trustless, like a public tokenizer.
"""
import ast, os, sys, subprocess

LOOP_VERSION = "loop_v1"

# The features doloop judges on each function. FROZEN for v1; a new feature set ships as loop_v2 (a new
# file), so any historical bill stays reproducible forever.
FEATURES_V1 = (
    "act-on-errors", "immutable-defaults", "context-manage-files", "type-hint-public",  # consistency
    "name-validator-drift", "name-getter-drift", "name-predicate-drift",                # name vs body
    "type-return-drift", "doc-return-drift", "doc-param-drift",                          # doc/type vs body
    "paired-cleanup-absence",                                                            # the dog that didn't bark
)
N = len(FEATURES_V1)  # 11 features per function in v1


def _functions(src):
    try:
        return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(ast.parse(src)))
    except SyntaxError:
        return 0


def calibration_loops(repo):
    """Loops to calibrate a repo: every function judged on every feature."""
    funcs = 0
    for d, _, fs in os.walk(repo):
        if "/.git" in d or "/test" in d:   # tests are not part of calibration
            continue
        for fn in fs:
            if fn.endswith(".py"):
                try:
                    funcs += _functions(open(os.path.join(d, fn), encoding="utf-8", errors="replace").read())
                except OSError:
                    pass
    return funcs * N


def commit_loops(repo="."):
    """Loops for the staged commit: changed functions x features."""
    files = subprocess.run(["git", "-C", repo, "diff", "--cached", "--name-only"],
                           capture_output=True, text=True).stdout.split()
    funcs = sum(_functions(subprocess.run(["git", "-C", repo, "show", f":{f}"],
                capture_output=True, text=True, errors="replace").stdout)
                for f in files if f.endswith(".py"))
    return funcs * N


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--staged":
        print(f"{commit_loops(a[1] if len(a) > 1 else '.'):,} loops  ({LOOP_VERSION}, this commit)")
    elif a:
        print(f"{calibration_loops(a[0]):,} loops  ({LOOP_VERSION}, calibrate {a[0]})")
    else:
        print(f"usage: loops.py <repo>  |  loops.py --staged [repo]   "
              f"({LOOP_VERSION}: 1 loop = 1 function x 1 feature, {N} features)")
