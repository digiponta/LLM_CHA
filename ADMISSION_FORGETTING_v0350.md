# LLM_CHA v0.3.5 — Admission & Forgetting Holdout Evaluation

Development branch `v0.3.0`; Stable Release v0.2.34 and `main` are unchanged.

## What changed
- Added standalone `admission_forgetting_v0350.py` with separate counters for first-time admission, admission rejection, eviction, auto-pin promotion and demotion.
- Added four independently authored synthetic holdout traces to compare the v0.3.3 policy with a separately instrumented v0.3.5 admission/forgetting evaluator over capacities 2/4/8.
- Admission rate measures admitted observations divided by admission attempts, **not** knowledge accuracy or an end-to-end conversation success rate.
- Queries do not insert topics. Explicit and auto protected slots are not silently evicted; a fully protected cache rejects admission.
- Unlike persistent Context Recovery, this evaluator does not save or restore forgotten topics. Any future restoration must still pass the current Corpus and Truth Gate validation.

## Validation
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py test_hybrid_retention_v0310.py test_adaptive_importance_v0320.py test_auto_pin_protection_v0330.py test_important_competition_v0340.py test_admission_forgetting_v0350.py
python admission_forgetting_v0350.py
```
Expected 78 tests (68 previous + 10 new), pending developer run. Evaluation yields 24 rows (4 scenarios × 3 capacities × 2 versions) in `results/admission_forgetting_v0350.json`.

## Limitations
The v0.3.5 algorithm is intentionally similar to v0.3.3 and chiefly instruments admission and forgetting. This phase does **not** claim an accuracy improvement. The holdout scenarios have not been used to tune thresholds; preserve them when exploring v0.3.6 and create additional unseen holdouts before final policy selection. No live `chat.py`, GPU, Semantic Memory or Truth Store integration.
