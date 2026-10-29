# v0.13.58.75 — LLM_SEM live vector retrieval

This branch adds a **real LLM_SEM checkpoint-backed vector scorer**; it does not alter LLM_CHA dialogue paths or training. It reads *only* query and candidate-question text from the reviewed CSV, never answer_reusable or labels for scoring. Uses LLM_SEM `LanguageModel.load_checkpoint`, `Tokenizer.load` and `semantic.encode_text` (default hybrid alpha 0.35). The checkpoint and tokenizer must be compatible.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.13.58.75-llm-sem-vector-retrieval
python -m unittest -v test_score_holdout_llm_sem_v0135875.py test_compare_holdout_retrieval_v0135874.py

python score_holdout_llm_sem_v0135875.py `
 --review data/holdout_answer_review_v0135872_ai_reviewed.csv `
 --sem-root ../LLM_SEM `
 --checkpoint ../LLM_SEM/model/model-sem-internalized-v01575.pt `
 --tokenizer ../LLM_SEM/model/tokenizer.json `
 --device cuda `
 --output results/llm_sem_scores_v0135875.csv

python compare_holdout_retrieval_v0135874.py `
 --review data/holdout_answer_review_v0135872_ai_reviewed.csv `
 --ranking results/llm_sem_scores_v0135875.csv `
 --output results/llm_sem_holdout_v0135875.json
```

**Check actual local model/tokenizer paths before running**; the checkpoint/tokenizer paths above are examples only. This version loads the LLM_SEM repo's public-facing semantic.py API as currently defined on GitHub. Scores measure semantic similarity of question to candidate question; they do not measure answer correctness or constitute an approved UNKNOWN gate. Use identical evaluation pairs and metrics for TF-IDF comparisons. Model output is unverified until local GPU execution completes.

Note: loading checkpoints should be performed only with locally trusted checkpoint files.
