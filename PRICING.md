# Pricing — the loop

doloop meters in **loops**. Loops are to doloop what tokens are to Claude — but
deliberately *not* tokens, because doloop is a deterministic do-learn **loop**,
not a stochastic AI.

Metering is **per-surface**:

- **Prose & document donkeys** — one check = one loop.
- **Code donkey** — one loop = **one function judged on one feature**. A commit
  costs `changed functions × features` loops; the public, frozen counter is
  [`loopmath.py`](../machine/loopmath/loopmath.py), so you reproduce the count, you never trust it.

The plans hide the loop the way Anthropic hides tokens behind Free / Pro / Max —
one loop underneath them all.

## Plans

| Plan | Price | Loops / month | Held to | Pooling | Adds |
|---|---|---|---|---|---|
| **Free** | $0 | 100 (anonymous) · **1,000** (GitHub sign-in) | the **world** (global pattern cache) | **on, mandatory** | — |
| **Pro** | **$20/mo** | **10,000** | your **own code** (auto-consistency, BYO repo) | on by default, can toggle off | auto-consistency |
| **Max** | **$200/mo** | **1,000,000** | sealed (hermetic, no egress) | **off** by default (regulatory) | hermetic mode |
| **Enterprise** | **Contact us** | custom / uncapped | sealed + on-prem option | off | SLA, dedicated support, custom ratchet |

- **Free is free because it's pooled.** You contribute the abstracted *lesson*
  from each loop back into the public donkeys — that's how you pay. Contribution
  is mandatory on Free. Anonymous gets 100 loops/month; sign in with GitHub for 1,000.
- **Pro** adds auto-consistency: bring your own repo and the donkey holds your
  code to *its own* conventions. Pooling stays on by default; you can turn it off.
- **Max** adds a hermetic, sealed mode with no egress, and pooling is off by
  default for regulatory use.
- **Enterprise** is for teams that outgrow Max: custom (uncapped) loops, an
  on-prem / sealed deployment, an SLA, dedicated support, and a dedicated ratchet.
  **[Contact us](mailto:hello@doloop.io).**

## Your bill is reproducible

```
bill = loops_used × published_rate
```

Both sides are public and reproducible. Run [`loopmath.py`](../machine/loopmath/loopmath.py)
on your own repo and you get the exact loop count we bill. Nothing about your
invoice is a black box.

## Privacy

Today: **BYOL — your model stays yours; we never train on your code.** Once the
local gate ships, your entire codebase never leaves your machine (snippets only).
We do not claim "nothing leaves" yet.

## How metering works

Send your doloop key as `Authorization: Bearer dlp_...`. Each metered call:

- charges loops (response header `x-doloop-loops-charged`)
- returns your remaining balance (response header `x-doloop-loops-remaining`)
- returns **HTTP 402** once your monthly loops are exhausted

The donkey verdict is identical whether the call is metered or free.
