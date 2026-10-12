# LLM_CHA v0.3.2 — Adaptive Importance & Auto-Pin Reallocation

Branch: `v0.3.0`; stable `v0.2.34` unchanged.

## Scope
Independent metadata-only policy in `adaptive_importance_v0320.py`, compared against v0.3.1 `hybrid`.

- Explicit pins: names listed in `explicit_topics`; **never auto-demoted**. If they fill capacity, admission fails safely.
- Automatic pins: requested only for fixture-labeled `Event(...,important=True)`; limited by `auto_budget` (default `capacity//2`) and eligible for demotion based on frequency and elapsed turns.
- Non-explicit topics can be replaced when capacity is reached; frequency, recency and auto protection affect victim selection.
- `query` is read-only and does not reinsert missing topics.
- No corpus facts, Truth State, Semantic Memory or model weights are changed.

## Run

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py test_hybrid_retention_v0310.py test_adaptive_importance_v0320.py
python -c "import json; from adaptive_importance_v0320 import compare; print(json.dumps(compare(), ensure_ascii=False, indent=2))"
```

Target **48** tests (38 established + 10 new), pending developer execution. `compare()` returns 30 rows (five scenarios, three capacities, two policies).

## Limitations
Auto-pin importance is provided by synthetic fixture labels, not inferred from natural language or Semantic Memory. This prototype does not implement live chat integration, long-term replay evaluation, or externally validated correctness. Automatic pin promotion/demotion is an experimental policy, not an assertion that any knowledge is TRUE. Compare both protected-topic returns and admission costs; no best-policy claim before results.
