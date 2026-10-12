# LLM_CHA v0.2.35.1 — Adaptive Retention Comparison

Branch: `v0.2.35-adaptive-context` (experimental). Stable tag `v0.2.34` remains untouched.

## Purpose

Evaluate three topic-retention policies against identical deterministic traces:
- **LRU**: evict least recently observed.
- **Frequency-Aware**: evict least frequently observed (LRU as tie-break).
- **Pin-Aware Adaptive**: protect explicitly important topics, evict oldest unpinned. Fail closed if capacity is fully pinned.

`Event(kind, topic, important)` supports `observe` and `query`. A query checks retention **before** any new observation and does not reinsert topics automatically. This avoids inflated return-success measurements.

Metrics: query return success rate, important-topic retention rate at query times, eviction count, capacity compliance, and refusal counts when all topics are pinned. These are simulation metrics, **not** live chat/GPU scores; an important topic means fixture-labeled importance, not inferred semantic importance. No Truth Gate bypass or knowledge writes.

## Run

```powershell
git switch v0.2.35-adaptive-context
git pull --ff-only origin v0.2.35-adaptive-context
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py
python adaptive_retention_eval_v023351.py
```

Expected **20 unit tests** (10 previous + 10 new), pending actual Windows results. Report: `results/adaptive_retention_v023351.json`. Evaluation only demonstrates the specific generated trace; further independent traces and sensitivity sweeps are needed before policy selection.

## Next

Compare diverse holdout traces (short/long gaps, balanced/imbalanced topics, heavy pinning), include explicit retention/forgetting costs, and then choose policy for an opt-in adapter to `MultiTopicContext`.
