# LLM_CHA v0.4.28.20 — Human-Labeled QA Relevance Calibration Worksheet

This release adds a non-destructive 64-turn CSV worksheet exporter. It uses the exact columns of the existing v0.4.28.13 review CSV importer, ordered with focus cases A04/A05/C05/C07 first, without inventing any relevance labels. The CSV includes question and final answer but not generation candidates; consult results/generation_gate_review_v042816.json when judging primary/probe fields. Explicitly enter true/false in the relevant review columns, or leave blank if not assessed.

PowerShell:

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile export_qa_review_worksheet_v042820.py
python -m unittest -v test_export_qa_review_worksheet_v042820.py test_prepare_qa_calibration_v042819.py

python export_qa_review_worksheet_v042820.py `
  --validation results/semantic_probe_validation_v042812.json `
  --output results/qa_review_worksheet_v042820.csv
```

To aggregate labels entered in the new worksheet:

```powershell
python prepare_qa_calibration_v042819.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/qa_review_worksheet_v042820.csv `
  --output results/qa_calibration_reviewed_v042820.json
```

The output filename must be new; no overwriting. Expected new tests: 5, expected cumulative tests: 101 pending Windows confirmation. Human labels are not auto-filled. Do not infer model accuracy or tune a classification threshold without diverse labeled positives and negatives and an independent holdout. This modifies only the v0.4.0 branch and does not touch chat.py, Truth Gate, Semantic Memory, /sleep, /train or model weights.
