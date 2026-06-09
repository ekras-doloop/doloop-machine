# doloop telemetry — design spec (for sign-off, not yet built)

> Status: **proposal**. Nothing is collected today; `/v1/check-code` stores nothing.
> This spec exists so the override flywheel can be switched on *without* breaking the
> promise the rest of the site makes: **your model stays yours; we never train on your
> code.** Telemetry gathers the lesson, not the code — only aggregated rule-hit metadata,
> never source.

## The one rule

**Gather the lesson, not the code.** Telemetry transmits no source, no file contents, no
file paths, no secrets, and no identifiers beyond an optional tenant id. What we may collect
is *aggregated rule-hit metadata* — counts, never code. (The check itself sends your code to
the server to be judged; your model stays yours and we never train on your code.)

## What we'd collect (the record)

One row per rule per language per week, aggregated:

```json
{ "rule_id": "CS-042", "severity": "fail", "language": "go",
  "week": "2026-W23", "fired": 1200, "overridden": 840, "fixed": 360,
  "tenant": null }
```

- `fired` — times the rule produced a finding.
- `overridden` — times a developer saw the finding and shipped anyway (see below).
- `fixed` — times the finding was gone on the next run of the same file.
- `tenant` — null for the anonymous pool; a tenant id only for a keyed, opted-in account
  (its own ratchet).

That is the entire payload. No snippet, no filename, no diff.

## How "override" is captured (deterministically, no source)

A developer overrides a finding by leaving an inline suppression:

```c
memcpy(bp, pl, payload);  // doloop:ignore CS-042  (reason optional)
```

The donkey counts the `doloop:ignore <rule>` token — the **rule id only**, never the line
it sits on. That gives a clean, countable override signal with zero source exposure. (A CI
run that fails and is then merged anyway is a weaker secondary signal we can add later.)

## Why the two signals are the product

- **Failure modes** (`fired` by rule × language) → which rules are load-bearing vs dead
  weight; surfaces emerging AI-code smells before anyone catalogs them.
- **Override rate** (`overridden / fired`) → the richest signal in the system. A high rate
  means one of two things, both actionable:
  - the rule is **noisy** → auto-demote it from the canonical corpus, or
  - the team's **house rules legitimately differ** → a ratchet candidate for their private
    overlay.

The canon tunes itself from real use: rules the world keeps overriding sink; rules everyone
fixes rise.

## Opt-in model (proposed defaults)

| Tier | Telemetry default | What's shared |
|---|---|---|
| **keyless / free** | **off** | nothing (matches the current promise) |
| **keyed (own ratchet)** | tenant-private | only the tenant's own aggregates, used for their ratchet; not pooled |
| **pool tier** | opt-in, anonymous | the `tenant: null` aggregate above, in exchange for a rate credit ([[cost-model-tiers]]) |

`doloop code` and the Action take `--no-telemetry` (and it is the default for keyless).

## Guarantees to publish alongside it

1. Telemetry transmits no source code, file contents, paths, or secrets, ever (the check itself sends your code to be judged; telemetry does not).
2. Collection is opt-in; keyless usage transmits nothing.
3. Only aggregated counts leave the machine; raw events are not retained.
4. Pool contributions are anonymous and abstracted (rule id + counts only).
5. The open corpus shows exactly which rules moved and why (override-driven), so the
   tuning is auditable.

## Open questions for sign-off

- Is `doloop:ignore CS-042` the override token we want (vs a config file, vs CI status)?
- Pool credit size per contributed aggregate?
- Do we publish the aggregate override stats openly (a public "AI code fails like this"
  report) as a marketing + research asset?
