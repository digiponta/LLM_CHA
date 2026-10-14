# v0.4.28.21 — Human QA Review Batch Planner

Read-only tool for making steady progress on manually labeling the existing 64-turn development benchmark. It validates the complete CSV against its original validation JSON using the v0.4.28.13 source-integrity checks, then generates batches (default 8) of rows whose `final_relevant` is blank. The four previously examined cases A04/A05/C05/C07 are listed first **as review priorities only**, not automatically given negative labels.

## Windows

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile plan_qa_manual_review_v042821.py
python -m unittest -v test_plan_qa_manual_review_v042821.py test_export_qa_review_worksheet_v042820.py

python plan_qa_manual_review_v042821.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/qa_review_worksheet_v042820_fixed.csv `
  --batch-size 8 `
  --output results/qa_review_plan_v042821.json
```

Review each batch's question and actual final answer. Enter `true`, `false`, or blank into the **existing CSV worksheet** `final_relevant` column. When re-running, use a new output path; outputs are never overwritten. Do not manually edit immutable question/answer metadata in the worksheet. After several annotations, rerun the v0.4.28.19 inventory using that same CSV and a new output name.

With a blank worksheet the expected summary is `total_turns=64`, `final_relevant_labeled=0`, `positive=0`, `negative=0`, `unlabeled=64`, with 8 batches.

New tests: five (pending Windows verification); related tests total ten. No threshold selection, classifier, or runtime change is performed. All examples are development-only. Independently collected holdout data is needed for generalization claims.
