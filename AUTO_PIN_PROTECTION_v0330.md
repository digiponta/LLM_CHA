# LLM_CHA v0.3.3 — Protected Auto-Pin Reallocation

Development branch: `v0.3.0`. Stable v0.2.34 remains unchanged.

## Motivation
v0.3.2 passed 48/48 tests but lost the delayed-return important topic under all three tested capacities. Its soft auto-pin bonus could be outweighed by age in the ordinary eviction score.

## Experiment
`auto_pin_protection_v0330.py` separates **eviction** from **pin reallocation**:
1. Explicit pins are never silently removed.
2. Active auto-pins are ineligible for normal eviction.
3. A new important topic receives a free auto-pin slot if one exists.
4. Only auto-pins unused for at least `min_age_for_reallocation` turns can be demoted when a new important topic enters; the new topic's observation count must meet the old one's count.
5. At least one capacity slot remains outside the auto-pin budget (except explicit pins can still fill the entire cache). When all entries are protected, new insertion is refused rather than discarding a protected topic.

## Test and comparison
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py test_hybrid_retention_v0310.py test_adaptive_importance_v0320.py test_auto_pin_protection_v0330.py
python auto_pin_protection_v0330.py
```

Expected: 58 total tests (48 + 10), pending local verification. Comparison: five scenarios × three capacities × three policies (v0.3.1 Hybrid, v0.3.2 Auto-Pin, v0.3.3 Protected Auto-Pin) = 45 rows. Report: `results/auto_pin_protection_v0330.json`.

## Important limitation
A protection guarantee and a guarantee that a new important topic is admitted cannot both hold when all slots are explicitly protected. Further, the current fixture introduces one old important topic, so delayed-return preservation does **not** prove accuracy under multiple competing important topics. No live chat, semantic truth assessment, GPU runtime or external persistence is changed.
