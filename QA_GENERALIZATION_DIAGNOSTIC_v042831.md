# LLM_CHA v0.4.28.31 — Generalization Diagnostic

Offline postprocessing of the already-produced v0.4.28.30 JSON. Reports counts and mean/min/max of **uncalibrated scores** separately by split and provisional ChatGPT label. Calculates a within-internal-holdout positive/negative pairwise ranking AUC *only if both labels exist*. It refuses duplicate keys, nonfinite or out-of-range scores, invalid split types and missing rows.

This is **not** an external independent holdout, **not** human ground truth, and **not** a deployable threshold or classifier accuracy estimate. AUC is a weak-label, internal development diagnostic with potentially very few positives. The training-side score distribution is in-sample and must not be presented as generalization evidence.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile diagnose_qa_generalization_v042831.py
python -m unittest -v test_diagnose_qa_generalization_v042831.py test_evaluate_qa_cross_encoder_v042830.py

python diagnose_qa_generalization_v042831.py `
  --input results/qa_cross_encoder_holdout_v042830.json `
  --output results/qa_generalization_diagnostic_v042831.json
```

Expected focused tests: 10 (5 new and 5 existing) pending Windows verification. Does not retrain or touch checkpoint, Truth Gate, generation model, Semantic Memory, /sleep, /train or chat.py. Next: share the generated report, inspect Holdout class counts and score direction. Collect genuinely unseen, independently reviewed QA pairs before stronger generalization claims.
