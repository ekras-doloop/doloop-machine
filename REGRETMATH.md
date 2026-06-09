# REGRETMATH — what a deviation costs if you leave it in

A deterministic number, not a vibe. Across 60 cross-release cases where a function broke its codebase's own convention, we measured how long the deviation sat before someone went back and fixed it, and the churn while it waited. doloop flags the same deviation at the commit, so your regret is zero.

| pattern | cases | typically fixed after | rework while it sat |
|---|---|---|---|
| `immutable-default` | 24 | ~3,697 commits later | ~927 churn |
| `act-on-errors` | 21 | ~2,426 commits later | ~813 churn |
| `dim-3:doc-param-drift` | 6 | ~665 commits later | ~1,345 churn |
| `type-hint` | 3 | ~1,952 commits later | ~188 churn |

**Overall:** a deviation is fixed a median of ~3,047 commits later. Caught at the commit, that is regret you do not pay.

## SAVEMATH
```
saved = bugs_caught x hours_per_bug x your_loaded_rate
```
Inputs yours, formula public.

## The loop
One loop = one function judged on one feature (frozen, reproducible via loopmath.py). A commit costs `changed_functions x features` loops. The plans hide the loop behind Free / Pro / Max / Enterprise. We deliberately do not publish a per-loop rate: the bill is `loops x the published rate`, both sides reproducible, so you do the math yourself. regretmath is the value side to weigh it against -- a deviation typically costs ~3,047 commits of delay if it is missed.
