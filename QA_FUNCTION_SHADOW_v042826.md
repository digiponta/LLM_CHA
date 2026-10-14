# LLM_CHA v0.4.28.26 — Conservative Answer-Function Shadow

This step adds an **independent, limited heuristic** for answer-function compatibility: greeting, self-identity, simple GPU/LLM definition elements, and uninformative abstentions. It is **not an embedding model, a semantic entailment system, or a trained QA relevance classifier**. The majority of inputs will correctly remain `ABSTAIN` rather than be guessed. `REVIEW_CANDIDATE` never blocks a reply; even "未学習です" can be appropriate for private or fabricated information, so it cannot be automatically rejected. `SUPPORTED` detects only some surface evidence and does not guarantee factual correctness.

Decisions use only question and final answer; ChatGPT labels, Gate resolution and Semantic Agreement are joined **afterward for auditing**. All existing labels are provisional AI judgments, not independent human ground truth.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile qa_function_shadow_v042826.py
python -m unittest -v test_qa_function_shadow_v042826.py test_qa_relevance_shadow_v042825.py

python qa_function_shadow_v042826.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --comparison results/gate_relevance_comparison_v042814.json `
  --output results/qa_function_shadow_v042826.json
```

Expected focused tests: 13 (7 new + 6 prior), not yet verified on Windows. Results are descriptive only; no deployment threshold, no learned representations, no runtime gate edits. Future work should implement a real semantic cross-encoder or NLI-based QA compatibility model using separate train/development and untouched holdout splits, with particular emphasis on protecting accurate paraphrases and sensible uncertainty answers.
