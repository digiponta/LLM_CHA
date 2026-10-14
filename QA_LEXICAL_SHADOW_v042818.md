# LLM_CHA v0.4.28.18 — QA Lexical Shadow Baseline

This release adds an **offline, read-only lexical baseline** for inspecting question/answer character bigram overlap. It is **not** a semantic relevance model, is not trained, and must not be used to reject live answers. Japanese paraphrases can have low lexical overlap despite being correct. A high lexical overlap can also accompany irrelevant or nonsensical answers.

The script joins the existing 64-turn v0.4.28.12 validation report with the v0.4.28.13 CSV human labels. Only explicitly labeled rows contribute to `paired_labels`, `paired_positive`, and `paired_negative`. A zero-label result is expected when the CSV is blank. No performance estimate or threshold is claimed.

PowerShell:

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile evaluate_qa_lexical_shadow_v042818.py
python -m unittest -v test_evaluate_qa_lexical_shadow_v042818.py test_shadow_qa_relevance_v042817.py

python evaluate_qa_lexical_shadow_v042818.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/semantic_relevance_review_v042813.csv `
  --output results/qa_lexical_shadow_v042818.json
```

Run the full previous suite as needed. The expected cumulative test count is 91 (86 previous + 5), pending verification by the Windows host. Output cannot overwrite existing files.

Next: add balanced human-reviewed positive and negative examples to the CSV, compare overlap distributions, and only then prototype an independently evaluated relevance model. Do not derive a relevance threshold from four hand-selected failures; reserve untouched cases for external validation.

This does not modify Truth Gate, `chat.py`, persona, Semantic Memory, model weights, /sleep, /train, or branches other than `v0.4.0`.
