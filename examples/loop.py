#!/usr/bin/env python3
"""The self-heal loop (the "doloop"): check your model's output, and if it
fails, feed the findings back to your model and try again, until it passes.

Bring your own model: replace `your_model()` with your provider call.
"""
import json
import urllib.request


def check(text):
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        "https://api.doloop.io/v1/check",
        data=body, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def your_model(prompt):
    # replace with your own provider call (OpenAI, Anthropic, local, ...)
    raise NotImplementedError("wire in your own model here")


def doloop(prompt, max_tries=3):
    out = your_model(prompt)
    for _ in range(max_tries):
        verdict = check(out)
        if verdict["verdict"] == "pass":
            return out
        notes = "; ".join(f["message"] for f in verdict["findings"])
        out = your_model(
            f"{prompt}\n\nRevise to fix these and return only the new text:\n{notes}\n\nPrevious:\n{out}")
    return out  # best effort after max_tries


if __name__ == "__main__":
    print(doloop("Write one tight sentence about deterministic checks."))
