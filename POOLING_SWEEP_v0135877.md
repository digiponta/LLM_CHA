# v0.13.58.77 — Exploratory LLM_SEM pooling sweep

Compares mean, last, attention and hybrid (alpha 0, .35, .5, .75, 1), using the *same* checkpoint/tokenizer and 24x56 evaluation pairs. No training and no runtime gate changes.

```powershell
git fetch origin
git switch v0.13.58.77-pooling-sweep
python -m unittest -v test_pooling_sweep_v0135877.py test_diagnose_semantic_retrieval_v0135876.py test_score_holdout_llm_sem_v0135875.py test_compare_holdout_retrieval_v0135874.py
python pooling_sweep_v0135877.py `
 --review data/holdout_answer_review_v0135872_ai_reviewed.csv `
 --sem-root ../LLM_SEM `
 --checkpoint ../LLM_SEM/model/model-sem-internalized-v01575.pt `
 --tokenizer ../LLM_SEM/model/tokenizer.json `
 --device cuda `
 --output results/pooling_sweep_v0135877.json
```

All labels are AI-reviewed provisional labels; use this as exploratory diagnostic/development data. Selecting hyperparameters on this holdout invalidates claims of final independent test performance. For a defensible final comparison, freeze configuration and run on a fresh untouched, independently reviewed holdout. Note this script reloads checkpoint per pooling configuration (slower but straightforward).
