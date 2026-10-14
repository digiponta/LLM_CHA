# LLM_CHA v0.4.28.25 — Independent QA Relevance Review Shadow

This is a **non-operative baseline**, not a learned semantic relevance classifier. The signal is zero character-bigram overlap between a question and its final answer. Such a response is queued as `REVIEW_CANDIDATE` only; overlap may be zero even for excellent paraphrased or short Japanese answers. `NO_FLAG` does not indicate relevance, and `NO_SIGNAL` means overlap unavailable.

The shadow decision is calculated without using the ChatGPT labels, original Truth Gate decision, or Semantic Agreement. After decisions, the report compares them against provisional ChatGPT annotations, which are **not human ground truth**. No threshold is trained, no runtime response is blocked, and all cases come from the same 64-turn development benchmark. Do not claim independent test performance.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile qa_relevance_shadow_v042825.py
python -m unittest -v test_qa_relevance_shadow_v042825.py test_analyze_chatgpt_qa_gate_v042824.py

python qa_relevance_shadow_v042825.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --comparison results/gate_relevance_comparison_v042814.json `
  --output results/qa_relevance_shadow_v042825.json
```

Expected focused unit tests: 12 (6 new + 6 prior); Windows execution pending. A review candidate is **not** an automatic rejection. Since the earlier audited set contains 29 ChatGPT-negative accepted answers, the generated report will count which of those have zero lexical overlap, but this is only retrospective coverage.

Next step: determine whether the baseline review queue is useful while preserving accepted relevant answers, then build a genuinely independent semantic QA evaluator and evaluate on separately collected data. This change does not touch Truth Gate, chat.py, model weights, Semantic Memory, /sleep, or /train.
