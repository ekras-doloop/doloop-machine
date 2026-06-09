#!/usr/bin/env python3
"""Bring your own model: point an OpenAI-compatible client at the machine.

Your key is forwarded to your provider and never stored; the verdict comes back
attached on the response (the `doloop` field and the `x-doloop-verdict` header).
Requires: pip install openai
"""
from openai import OpenAI

client = OpenAI(api_key="YOUR_PROVIDER_KEY", base_url="https://api.doloop.io/v1")

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize deterministic checks in one sentence."}],
)

print(resp.choices[0].message.content)
# the verdict rides along on resp.doloop and the x-doloop-verdict response header
