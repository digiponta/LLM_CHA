# v0.13.58.76 — Semantic retrieval diagnostics

No model retraining or runtime integration. This change diagnoses the real 1,344 LLM_SEM cosine scores using provisional AI review labels.

```powershell
git fetch origin
git switch v0.13.58.76-semantic-retrieval-diagnostics
python -m unittest -v test_diagnose_semantic_retrieval_v0135876.py test_score_holdout_llm_sem_v0135875.py test_compare_holdout_retrieval_v0135874.py

python diagnose_semantic_retrieval_v0135876.py `
 --review data/holdout_answer_review_v0135872_ai_reviewed.csv `
 --ranking results/llm_sem_scores_v0135875.csv `
 --output results/semantic_retrieval_diagnostics_v0135876.json
```

Outputs: positive/negative cosine distributions, per-query positive-vs-negative margin and top-5 candidates with labels. Beware aggregate pairs share queries; positive and negative pairs are not statistically independent. Do not optimize hyperparameters on this same final test set and claim an independent heldout score. If tuning pooling/alpha, use a separate development set and reserve this holdout for one final evaluation.
