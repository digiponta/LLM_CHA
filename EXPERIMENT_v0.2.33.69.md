# LLM_CHA v0.2.33.69 — Human-Gold Epistemic Evaluation & Error Analysis

The previous release successfully created an eight-mention worksheet but reported `reviewed_count=0`, `metrics=null`. This release adds a **review-only** evaluator, with no invented gold labels.

- Validate corpus SHA-256, exact occurrence count, ordered byte offsets, sentence context, and context SHA-256 before scoring.
- Require explicit `review_status: "REVIEWED"` plus allowed nonempty `gold_labels`. An unreviewed row must have `gold_labels: null`.
- Compare v0.2.33.67 baseline versus v0.2.33.68 candidate using micro precision/recall/F1 and **per-label** TP/FP/FN, precision, recall, F1, and error examples.
- Report metrics **only for reviewed rows**, including partial review counts. The reference corpus and Semantic Memory remain untouched.
- Classification labels express rhetorical/epistemic style, **not Truth State**.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.69
git pull origin v0.2.33.69
python -m py_compile epistemic_review_analysis_v023369.py
python -m unittest -v test_epistemic_review_analysis_v023369.py test_epistemic_calibration_v023368.py
Copy-Item results/epistemic_calibration_v023368.json results/epistemic_gold_review_v023369.json
```

Edit `results/epistemic_gold_review_v023369.json`: review each sentence independently and set its `gold_labels` to an array of labels (e.g. `["ANALOGY","OPINION"]`) and `review_status` to `REVIEWED`. Keep `concept`, SHA, offsets, context and predictions unchanged.

```powershell
python epistemic_review_analysis_v023369.py --review results/epistemic_gold_review_v023369.json
```

To save without overwriting an existing output:

```powershell
python epistemic_review_analysis_v023369.py --review results/epistemic_gold_review_v023369.json --output results/epistemic_error_analysis_v023369.json
```

Until any human labels are provided, `reviewed_count=0`, `metrics=null`, `by_label=null` is **expected**. Avoid claiming measured classification accuracy from unit tests alone. Next: review eight original passages, analyze disagreements, then consider revisions with independent held-out data.
