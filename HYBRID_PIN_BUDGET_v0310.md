# LLM_CHA v0.3.1 — Hybrid Pin Budget Experiment

Branch `v0.3.0` (development); stable tag `v0.2.34` unchanged.

## Hypothesis
Always-pin strategy can prevent admission of new topics at saturation. Limit the **hard pin budget** to `max(1, capacity // 2)`; keep the remaining slots evictable using cumulative observation frequency, recency, and a lexical tie-break. When the budget is exhausted, an important new topic **may be admitted without a hard pin** and a `pin_budget_denials` counter is incremented. Existing hard pins are not silently removed.

## Components
- `hybrid_retention_v0310.py`: `hybrid(events, capacity, pin_budget)`; `compare()` evaluates LRU, frequency-aware, unbounded pin-aware, and budgeted hybrid across 5 synthetic scenarios × 3 capacities × 4 policies = 60 conditions.
- `test_hybrid_retention_v0310.py`: 10 unit tests.

## Local validation
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py test_hybrid_retention_v0310.py
python hybrid_retention_v0310.py
```
Expected 38 tests; **pending actual local execution**. Results in `results/hybrid_retention_v0310.json`. The experiment is not connected to `chat.py`.

## Interpretation
Pin budget denials and topic insertion refusals are **different metrics**. A pin denial may still admit the new topic. Query metrics test retained topic membership only; they do not measure correctness, corpus truth or downstream generation. Pin labels are manually assigned in test fixtures. The prototype uses a cumulative frequency counter (no decay), which is another hypothesis to validate.

## Next
Study admission/forgetting trade-offs including newly important topics and frequent long-term topics across holdout traces. Define a policy-level outcome criterion before integrating under an opt-in flag; maintain v0.2.34 Truth Gate / restore checks.
