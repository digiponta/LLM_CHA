# LLM_CHA v0.4.28.32 — Generalization Failure Analysis

Offline analysis of frozen `results/qa_cross_encoder_holdout_v042830.json`. The tool reuses v0.4.28.31 validation and compares each internal-holdout ChatGPT-weak-label Positive score against each Negative score, reporting correct, tied and inverted rankings plus the worst inverted pairs and train/holdout class summary.

The pairs share examples and thus are **not independent observations**. Holdout AUC is an internal, provisional diagnostic, **not externally validated performance**. A low AUC cannot distinguish undertraining, label error, distribution shift or memorization on its own. No new learning, calibration, threshold tuning, Truth Gate changes, or runtime usage.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile inspect_qa_ranking_failures_v042832.py
python -m unittest -v test_inspect_qa_ranking_failures_v042832.py test_diagnose_qa_generalization_v042831.py

python inspect_qa_ranking_failures_v042832.py `
  --input results/qa_cross_encoder_holdout_v042830.json `
  --output results/qa_ranking_failures_v042832.json
```

Expected focused tests: 10 (5+5), pending Windows verification. Inspect the resulting Holdout class counts before conclusions. To associate pair IDs with question/answer text, use the existing contract or original validation by exact ID and turn; no text is embedded in this diagnostic output.
