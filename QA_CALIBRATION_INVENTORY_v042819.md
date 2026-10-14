# LLM_CHA v0.4.28.19 — QA Relevance Calibration Inventory

This release adds a read-only inventory for the existing 64-turn development benchmark. It **does not label answers automatically**, and does not modify any model, Truth Gate behavior, persona, Semantic Memory, or learning path.

It reads the v0.4.28.12 validation JSON and v0.4.28.13 human review CSV. Rows are grouped by unlabeled focused examples (A04/A05/C05/C07), other unlabeled cases, and labeled cases. It reports counts of human-labeled relevant, irrelevant, and unlabeled answers, plus a character-bigram lexical overlap diagnostic. A label is available only after the user has explicitly filled in `final_relevant` with true or false. No acceptance error rate or semantic classification quality is established by this inventory.

The field `balanced_binary_calibration_ready` denotes **presence of at least one label from each class**, not quantitative class balance, sufficiently large sample size, or an independent holdout. Do not tune a threshold or assert generalization from the four focus examples.

## Windows PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile prepare_qa_calibration_v042819.py
python -m unittest -v `
  test_prepare_qa_calibration_v042819.py `
  test_evaluate_qa_lexical_shadow_v042818.py `
  test_shadow_qa_relevance_v042817.py

python prepare_qa_calibration_v042819.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/semantic_relevance_review_v042813.csv `
  --output results/qa_calibration_inventory_v042819.json
```

Expected 15 focused tests (5 new + 10 previous) and 96 cumulative unit tests (91 previous + 5), pending Windows verification. Report files are never overwritten.

Next, review the actual question/answer content and collect multiple diverse positive and negative labels. Freeze a truly independent test set before evaluating any new automatic relevance predictor.
