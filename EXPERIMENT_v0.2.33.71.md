# LLM_CHA v0.2.33.71 — Epistemic Classification Stabilization

v70 was verified by the user on 8 AI-assisted development holdouts (micro F1 90%, with 1 FP and 1 FN), while **H01** remained incorrectly labeled CONTEXT_ONLY: `私の解釈では、この現象は別の説明も可能だ。`

The offline v71 classifier adds explicitly first-person stance patterns (`私の解釈では`, `私の見解では`, `私見では`, `個人的には`) without treating bare technical `可能性` as speculative. It preserves the fail-closed ambiguous `量子力学的には` behavior.

## PowerShell verification

```powershell
git fetch origin
git switch v0.2.33.71
git pull origin v0.2.33.71
python -m py_compile epistemic_stabilization_v023371.py
python -m unittest -v test_epistemic_stabilization_v023371.py test_epistemic_holdout_v023370.py
python epistemic_stabilization_v023371.py
Copy-Item results/epistemic_prospective_v023371.json results/epistemic_prospective_review_v023371.json
```

Open the review copy and annotate each of 12 `context` fields independently: `gold_labels` array and `review_status: REVIEWED`. Do not edit the provided sentences or predictions.

```powershell
python epistemic_stabilization_v023371.py --score results/epistemic_prospective_review_v023371.json
```

Unreviewed worksheet -> `metrics: null`. Inputs were prospectively fixed **before this run**, but authored after seeing model weaknesses and **not a final independent corpus**. This branch does not change `chat.py`, Semantic Memory, Truth State or LLM weights. No user-side test results are claimed until logs are shared.
