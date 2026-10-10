# LLM_CHA v0.2.33.44 — Clarification Robustness Audit

## Purpose

Measure weaknesses of the existing **unchanged** v0.2.33.40 and v0.2.33.43 clarification policies using fresh, developer-authored diagnostic cases. Six development cases and eight separately labeled final cases cover negation, contradictory/multiple choices, indirect topic switches, politely expressed answers, canonical choices and uncertainty.

The final cases are **not a representative independent benchmark**: they were designed by the experiment developer, though split text is disjoint and the policy is not edited in response to final data. Each case runs both arms with the same first input and follow-up in fresh temporary shadow stores.

Success uses **status and canonical value** where appropriate; it checks zero approved records without explicit confirmation. Diagnostics must be inspected by case, not only by overall percentage.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.44
git pull origin v0.2.33.44
python -m py_compile clarification_robustness_v023344.py
python -m unittest -v test_clarification_robustness_v023344.py test_clarification_normalization_v023343.py
python clarification_robustness_v023344.py
```

Output: `results/clarification_robustness_v023344.json` (refuses overwrite).

## Limitations and follow-on

Do not tune the existing policies against the held-out final split and then continue to call it held-out. An observed `clarify` status may occur for the wrong reason; next version should assess whether the question actually addresses the new user intent and whether clarification succeeds within a bounded number of turns. Production Semantic Memory, model training, stable runtime, and /sleep remain untouched.
