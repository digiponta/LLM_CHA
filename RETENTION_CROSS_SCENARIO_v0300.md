# LLM_CHA v0.3.0 — Cross-Scenario Context Retention

Development branch: `v0.3.0`, created from `v0.2.35-adaptive-context`. The stable `v0.2.34` tag and `main` are unchanged.

## Scope

This experiment extends v0.2.35.1 to five independently authored deterministic test scenarios: short topic switching, delayed return, frequency skew, saturation of pinned topics, and heavy topic churn. Run LRU, frequency-aware, and pin-aware policies under capacities 2, 4, 8 (45 results).

`retention_cross_scenario_v0300.py` outputs a structured JSON report. A protected insertion refusal is a measurable cost: a pinned topic survives, but a new pinned topic may not enter when capacity is exhausted. Policies must be compared on both retention and acceptance, not only pinned-topic survival.

The evaluator is synthetic and **not** yet connected to live `chat.py`, Semantic Memory, Truth State or GPU generation. A query is a read-only check of current topic retention and cannot change the cache. No production policy is selected by this file.

## Run (PowerShell)

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.3.0
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py
python retention_cross_scenario_v0300.py
```

Expected unit tests: 10 + 10 + 8 = **28**, pending user-side validation.

Report: `results/retention_cross_scenario_v0300.json`.

## Next
Review per-scenario outcomes, compare capacity-sensitive trade-offs, implement an adaptive pin budget or eviction-with-priority only if tests motivate it, then integrate behind an opt-in feature flag, retain all v0.2.34 Truth Gate checks and run old release regression plus GPU acceptance.
