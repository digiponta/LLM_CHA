# LLM_CHA v0.4.28.22 — Human-labeled QA lexical comparison

Read-only descriptive analysis of the existing 64-turn development set. This is **not** semantic relevance classification. Comparisons appear only when the human-reviewed CSV contains at least one positive and one negative label with a defined lexical overlap. A difference in means on this dataset is not a generalization estimate. The tool does not optimize thresholds, estimate model accuracy, or alter Truth Gate.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m py_compile compare_labeled_qa_v042822.py
python -m unittest -v test_compare_labeled_qa_v042822.py test_plan_qa_manual_review_v042821.py

python compare_labeled_qa_v042822.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/qa_review_worksheet_v042820_fixed.csv `
  --output results/qa_labeled_comparison_v042822.json
```

A blank review CSV yields positive=0, negative=0, unlabeled=64, between_class_comparison_available=false and difference_in_means=null. To progress, manually inspect the actual final answers and record true/false in final_relevant; a separate independent holdout is needed before choosing operating thresholds. Semantic agreement is explicitly NOT_AVAILABLE_IN_THIS_INPUT; do not mistake character bigram overlap for semantic agreement.

Expected tests: five new (ten across the two listed test modules), pending user Windows verification. No changes to chat.py, models, memory, /sleep or /train.
