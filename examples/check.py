#!/usr/bin/env python3
"""Check an AI output against the doloop donkeys.

Deterministic: the same text returns the same verdict and the same input_sha256
every time. No SDK and no API key needed for /v1/check.
"""
import json
import urllib.request


def check(text):
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        "https://api.doloop.io/v1/check",
        data=body,
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


if __name__ == "__main__":
    result = check("It is worth noting that, in many ways, this is slop.")
    print("verdict:", result["verdict"])
    print("sha256 :", result["input_sha256"])
    for f in result["findings"]:
        print(f"  - [{f['layer']}] {f['message']}")
