#!/usr/bin/env bash
# CI gate: run a file's text through the donkeys; exit nonzero if it fails.
# Usage: ci_check.sh <file>
set -euo pipefail
FILE="${1:?usage: ci_check.sh <file>}"

PAYLOAD=$(python3 -c 'import json,sys; print(json.dumps({"text": open(sys.argv[1]).read()}))' "$FILE")
VERDICT=$(curl -s https://api.doloop.io/v1/check \
  -H 'content-type: application/json' \
  --data "$PAYLOAD" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["verdict"])')

echo "doloop verdict: $VERDICT"
[ "$VERDICT" = "pass" ] || { echo "blocked by doloop"; exit 1; }
