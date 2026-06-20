# doloop machine

An external, **deterministic** check you put between your AI and your users. Send it an output, get back an **objective verdict** — the same verdict every time, with the exact findings and where each one is. You bring your own model; the machine never touches it.

> This repo is **docs + the CLI**. The donkey rules run server-side; nothing here holds them.

- **Base URL:** `https://api.doloop.io`
- **Install the CLI:** `pip install doloopio`
- **Get a key / dashboard:** https://api.doloop.io/dashboard
- **Site:** https://doloop.io · **Pricing:** [PRICING.md](PRICING.md)

## 60-second start

No install, from the shell:

```bash
curl https://api.doloop.io/v1/check \
  -H 'content-type: application/json' \
  -d '{"text": "the answer your model just produced"}'
```

Or the CLI:

```bash
pip install doloopio
doloop check "the answer your model just produced"
echo "..." | doloop check                       # stdin
doloop check -f draft.md && publish draft.md     # exit 0 = pass, 2 = fail
```

Response:

```json
{ "verdict": "pass", "finding_count": 0, "findings": [], "input_sha256": "9f2…", "version": "0.1.0+lex.e8e63c5f" }
```

Same text in, the same verdict out, every run — byte-identical on the mechanical lenses, where `input_sha256` + `version` make it reproducible: identical input + identical version → identical verdict. (The vision-model and the pinned, advisory linguistic reader are not byte-deterministic; see [Determinism](#determinism).) **Objective, not subjective** — unlike an AI judge that scores the same answer 77% one run and 63% the next.

## The donkeys

A donkey is a deterministic check for one kind of output. Choose one with the `donkey` field (default `writing`).

| Donkey | Catches | Endpoint |
|---|---|---|
| `writing` | de-slop: dead prose, jargon, self-management tics, flat cadence | `POST /v1/check` |
| `conversations` | de-sycophant, de-loop: agreement drift, a dialogue going in circles | `POST /v1/check` with `"donkey":"conversations"` |
| `presentations` | land-the-finding: a chart or slide that buries the point | `POST /v1/check-chart` (image) |
| `documents` | tie-out: a number not in the source, a total that won't reconcile | runs at `wysiwyd.doloop.io` |
| `design` | visual-hierarchy hygiene: font / weight / width / color sprawl on a live page | `POST /v1/check-design` (url) |
| `code` | the commit gate: the conventions your codebase already keeps | `POST /v1/check-code` (code) |

```bash
curl https://api.doloop.io/v1/donkeys     # the live roster
```

## Auth & plans

The standard check is **keyless and free** on the **Free** plan (sign in with GitHub for more). Free is free because it's pooled: you contribute the abstracted lesson back to the public donkeys. Bring a **doloop key** (`dlp_…`, from the dashboard) for **Pro** ($20/mo, auto-consistency against your own code), **Max** ($200/mo, hermetic), or **Enterprise** (contact us, on-prem) — metered against your balance, applying your private house rules (the ratchet). *Metering is being finalized; see [PRICING.md](PRICING.md).*

```bash
# keyless: free tier
curl https://api.doloop.io/v1/check -H 'content-type: application/json' -d '{"text":"..."}'

# keyed: metered, applies your house rules, returns balance headers
curl https://api.doloop.io/v1/check \
  -H 'authorization: Bearer dlp_your_key' \
  -H 'content-type: application/json' \
  -d '{"text":"..."}'
# returns your remaining balance in the response headers

# CLI
export DOLOOP_KEY=dlp_your_key
doloop balance        # balance remaining
```

Metering is per-surface and reproducible; the details are being finalized. See [PRICING.md](PRICING.md).

## Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/v1/check` | `{"text", "donkey"?}` | verdict + findings + `input_sha256` |
| `POST` | `/v1/check-code` | `{"code", "language"?}` | verdict + findings (code donkey) |
| `POST` | `/v1/check-design` | `{"url"}` | verdict + findings + counts (design donkey) |
| `POST` | `/v1/check-chart` | `{"image_url"}` or `{"image_b64"}` | verdict + findings (presentations, vision) |
| `POST` | `/v1/orchestrate` | `{"text"?, "dialogue"?, "chart_url"?, "chart_b64"?}` | one call over a bundle, merged verdict |
| `GET`  | `/v1/balance` | — (Bearer `dlp_` or `dbt_`) | `{"loops_remaining"}` |
| `GET` / `POST` | `/v1/rules` | (Bearer `dlp_`) | read / add your house rules |
| `POST` | `/v1/chat/completions` | OpenAI-shaped | BYOL proxy, verdict attached |
| `GET`  | `/v1/donkeys` | — | the roster |
| `GET`  | `/health` | — | liveness |

Machine-readable: [openapi.json](openapi.json) · LLM index: [llms.txt](llms.txt).

### `POST /v1/check` — text

```bash
curl https://api.doloop.io/v1/check -H 'content-type: application/json' \
  -d '{"text":"Furthermore, it is important to leverage synergies going forward.","donkey":"writing"}'
```

```json
{ "verdict": "fail", "finding_count": 3,
  "findings": [ { "layer": "writing", "check": "chronos_hedge", "severity": "fail",
                  "line": 1, "message": "...", "evidence": "going forward" } ],
  "input_sha256": "…", "version": "0.1.0+lex.…" }
```

### `POST /v1/check-design` — a live URL

```bash
curl https://api.doloop.io/v1/check-design -H 'content-type: application/json' \
  -d '{"url":"https://your-site.com"}'
```

```json
{ "verdict": "pass",
  "findings": [ { "severity": "warn", "message": "35 distinct colors. A tight palette is ~8-12." } ],
  "counts": { "font_sizes": 6, "weights": 4, "widths": 5, "colors": 35 } }
```

### `POST /v1/check-code` — a code snippet

```bash
curl https://api.doloop.io/v1/check-code -H 'content-type: application/json' \
  -d '{"code":"def f(x):\n    return x","language":"auto"}'
```

### `POST /v1/check-chart` — a chart image

```bash
curl https://api.doloop.io/v1/check-chart -H 'content-type: application/json' \
  -d '{"image_url":"https://example.com/chart.png"}'
```

### `POST /v1/orchestrate` — a multi-part bundle in one call

```bash
curl https://api.doloop.io/v1/orchestrate -H 'content-type: application/json' \
  -d '{"text":"the prose","dialogue":"User: ...\nBot: ...","chart_url":"https://…/c.png"}'
```

## Patterns (runnable)

1. **Gate before ship** — [examples/check.sh](examples/check.sh)
2. **Self-heal loop** (the "doloop": check → feed `findings` back to your model → re-check → ship on pass) — [examples/loop.py](examples/loop.py)
3. **In-agent self-check** (the agent checks its own step to catch the loop/drift it can't see) — [examples/agent_check.py](examples/agent_check.py)
4. **BYOL proxy** (point an OpenAI-compatible `base_url` at the machine) — [examples/proxy.py](examples/proxy.py)
5. **CI gate** (fail the build on a regression) — [examples/ci_check.sh](examples/ci_check.sh)

## Gate it in CI (GitHub Action)

Make the donkey a required check on every pull request:

```yaml
# .github/workflows/doloop.yml
name: doloop
on: [pull_request, push]
jobs:
  code-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: ekras-doloop/doloop-machine@main
```

It checks the code files changed in the push or PR and **fails the build** on any `fail` verdict, citing the rule and the line. Pin specific paths with `with: { paths: "src/**/*.py" }`, or meter against your key and apply your house rules with `env: { DOLOOP_KEY: ${{ secrets.DOLOOP_KEY }} }`. The same gate runs locally as `doloop code file.c` (exit 1 on a fail).

## Determinism

The verdict is byte-identical where determinism can be had — the **mechanical lenses**. The mechanistic donkeys use regex + statistics only: no randomness, no network, no time in the scoring. Same input → same `input_sha256` → same verdict. The reported `version` folds in the rule/lexicon hash, so any rule change is visible in the version: a verdict you can replay and audit, not an opinion. (Deterministic rule-based processing; see the model-risk note at https://doloop.io/model-risk/.)

Two paths are **not** byte-deterministic: the vision-model path (presentations) and the linguistic layer, which runs as a pinned, advisory reader. Those return findings the same shape as the rest, but they are advisory rather than byte-replayable.

## What it is

doloop is the external checker a model can't be for itself, because a model in a loop can't see its own loop. Bring your model; doloop returns the verdict it can't give itself.
