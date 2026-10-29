# v0.13.58.74 — Holdout Retrieval Benchmark

Experimental evaluation-only branch. No changes to chat.py, model weights, /sleep or approval policies.

## Inputs
- Reviewed pair CSV: data/holdout_answer_review_v0135872_ai_reviewed.csv (user-provided, **AI reviewed, not human approved**).
- Independent ranking CSV: query_id,candidate_id,score, one row per reviewed pair; higher score means more relevant.
- Do not generate scores from answer_reusable labels: that would leak the ground truth.

## Run (PowerShell)
```powershell
python -m unittest -v test_compare_holdout_retrieval_v0135874.py
python compare_holdout_retrieval_v0135874.py `
  --review data/holdout_answer_review_v0135872_ai_reviewed.csv `
  --ranking results/llm_sem_scores_v0135874.csv `
  --output results/llm_sem_holdout_v0135874.json
```

Metrics: oracle coverage, Hit@1/3/5 and MRR on queries with at least one reusable answer, and UNKNOWN top-1 reusable count. These do **not** establish independent label truth, human approval, real-world accuracy, or runtime false-accept rate. Obtain real LLM_SEM scores using a separate adapter under the same 24x56 input; do not claim that adapter is implemented by this branch.

For comparable TF-IDF scores, emit an identically shaped CSV from a separate lexical scorer. Keep calibration data independent of test questions.
