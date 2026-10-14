# LLM_CHA v0.4.28.27 — Two-Shadow Cross-Tab Diagnostic

Retrospectively compare the v0.4.28.25 lexical zero-overlap review flag against the v0.4.28.26 conservative answer-function review flag. This tool uses the **original question and answer for decision-making** via both existing modules; ChatGPT labels and original Truth Gate outcomes are used only afterwards to summarize cases. A flag means *review requested*, not rejection; SUPPORTED never guarantees factual truth; ABSTAIN is unknown. The field `either_review_descriptive` is a retrospective union count, **NOT a deployable OR rule**.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile compare_qa_shadows_v042827.py
python -m unittest -v test_compare_qa_shadows_v042827.py test_qa_function_shadow_v042826.py

python compare_qa_shadows_v042827.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --comparison results/gate_relevance_comparison_v042814.json `
  --output results/qa_two_shadow_comparison_v042827.json
```

Expected focused tests: 12 (5 new, 7 previous), pending Windows verification. The output includes the joint decision matrix, overlaps, and ChatGPT-provisional negative/positive coverage. It is a development-only analysis on the same 64 examples, not independent validation and not an accuracy estimate. No model, runtime, Truth Gate, Semantic Memory, /sleep or /train edits.
