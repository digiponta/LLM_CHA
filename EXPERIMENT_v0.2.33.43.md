# LLM_CHA v0.2.33.43 — Clarification Intent Normalization

Adds a narrow, auditable `ANSWER / SWITCH / UNCERTAIN` preprocessing layer above the v0.2.33.40 bridge. It targets three diagnostic failures in v0.2.33.42: `カーソルの方`, `意味記憶の実験`, and `別件を先に相談したい`.

The normalizer only accepts **exact** whitelisted answer aliases. It does not infer approval from a user phrase, does not promote a pending candidate, and does not interpret negated or compound answers as canonical values. A recognized indirect topic switch discards a pending candidate and hands off to the **real existing DSS purpose controller**, which may ask a fresh question. No production Semantic Memory or LLM parameters are modified.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.43
git pull origin v0.2.33.43
python -m py_compile clarification_normalization_v023343.py
python -m unittest -v test_clarification_normalization_v023343.py test_heldout_clarification_eval_v023342.py
python clarification_normalization_v023343.py --demo
```

Output: `results/clarification_normalization_v023343.json` plus experimental `results/normalization_shadow_v023343.json`. Both refuse overwrite.

## Evaluation boundary

The v0.2.33.42 probes were examined **before** defining these matching rules and therefore are **development cases**, no longer held-out for v0.2.33.43. Even if regression tests pass all 12, this does not demonstrate improved generalization. Next release should obtain an independent, locked, human-annotated test set with negation, conflicting answers, confirmation fatigue, switch precision, and context versioning.
