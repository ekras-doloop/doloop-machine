#!/usr/bin/env python3
"""In-agent self-check: after each step, run the step's output through doloop
before letting the agent continue.

A model in a loop cannot see its own loop. doloop can. Use this to catch the
agent slipping, repeating, or drifting that the agent will not catch itself.
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


def step_ok(step_output):
    verdict = check(step_output)
    if verdict["verdict"] == "fail":
        print("doloop blocked this step:")
        for f in verdict["findings"]:
            print(f"  - [{f['layer']}] {f['message']}")
        return False
    return True


if __name__ == "__main__":
    looping_output = "We we we keep going in circles, in circles, in circles."
    print("ship this step?", step_ok(looping_output))
