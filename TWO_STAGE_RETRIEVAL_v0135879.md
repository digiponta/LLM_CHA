# v0.13.58.79 — Experimental Two-Stage Retrieval

Stage 1 ranks candidate questions by character 2/3-gram TF-IDF and keeps K=5 or 10. Stage 2 reranks shortlisted candidates by normalized weighted lexical/LLM_SEM mean cosine scores (lambda=.5,.75,1). A *diagnostic threshold* is swept from 0 through .8. No runtime gate is modified.

\`\`\`powershell
git fetch origin
git switch v0.13.58.79-two-stage-retrieval
python -m unittest -v test_two_stage_retrieval_v0135879.py test_hybrid_retrieval_v0135878.py test_pooling_sweep_v0135877.py test_diagnose_semantic_retrieval_v0135876.py test_score_holdout_llm_sem_v0135875.py test_compare_holdout_retrieval_v0135874.py
python two_stage_retrieval_v0135879.py \`
 --review data/holdout_answer_review_v0135872_ai_reviewed.csv \`
 --sem-root ../LLM_SEM \`
 --checkpoint ../LLM_SEM/model/model-sem-internalized-v01575.pt \`
 --tokenizer ../LLM_SEM/model/tokenizer.json \`
 --device cuda \`
 --output results/two_stage_v0135879.json
\`\`\`

Evaluation separates eligibility based on whether **any** answer is reusable, NOT simply KNOWN/UNKNOWN labels. Acceptance precision is conditional on accepted answers, while false-accept rate across all queries and among no-positive queries is also given. Threshold choice on this set is development-only; select and freeze parameters before an untouched independent holdout.
