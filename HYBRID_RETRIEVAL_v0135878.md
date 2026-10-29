# v0.13.58.78 Hybrid Retrieval (exploratory)

This experiment uses TF-IDF-style **character 2/3-gram** weights (IDF fitted on 56 candidate questions) and the local LLM_SEM checkpoint with **mean** pooling. Each query's scores are normalized separately within each modality using min-max, then fused with lexical weight lambda=0, .25, .5, .75, 1. This is a development sweep, NOT a final independent Holdout.

```powershell
git fetch origin
git switch v0.13.58.78-hybrid-retrieval
python -m unittest -v test_hybrid_retrieval_v0135878.py test_pooling_sweep_v0135877.py test_diagnose_semantic_retrieval_v0135876.py test_score_holdout_llm_sem_v0135875.py test_compare_holdout_retrieval_v0135874.py

python hybrid_retrieval_v0135878.py `
 --review data/holdout_answer_review_v0135872_ai_reviewed.csv `
 --sem-root ../LLM_SEM `
 --checkpoint ../LLM_SEM/model/model-sem-internalized-v01575.pt `
 --tokenizer ../LLM_SEM/model/tokenizer.json `
 --device cuda `
 --output results/hybrid_retrieval_v0135878.json
```

Important: the lexical implementation may not exactly reproduce the previous TF-IDF baseline, so lambda=1 must be treated as a freshly measured baseline. The script does not change chat.py, weights, /sleep or unknown acceptance. All scoring is based on question and candidate question text only, not labels. No final selection or deployment is automated.
