# LLM_CHA v0.4.11 — Japanese Proposition Generalization Diagnostics

Adds `evaluate_japanese_proposition_v0411.py`: **20 hand-authored examples** to measure the *existing unmodified v0.4.10* rule-based extractor. Coverage includes supported copulas, nested parentheticals, new positive formats (`XとはYである`, `XはYを指す`, etc.) and negatives (different subject, mere mention, negation, quotation, question, hypothetical). Reports a confusion matrix (TP/FP/FN/TN), precision, recall, balanced accuracy, and per-case results.

**Important:** This is a small, manually constructed diagnostic, **not an independent held-out benchmark** and not evidence of real-world generalization. Some negative/positive labels encode intended *definition extraction* policy rather than ontological correctness. The evaluator does not edit the extractor or the source repository's truth rules, train models, ingest Wikipedia, or mutate any Semantic Memory. Every synthetic evidence record uses an `UNVERIFIED` flag. Score interpretation should focus on false-positive types and false-negative coverage before deciding any new parsing logic.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v test_evaluate_japanese_proposition_v0411.py test_article_proposition_alignment_v0410.py
python evaluate_japanese_proposition_v0411.py --report results/japanese_proposition_generalization_v0411.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Share the JSON report to identify which specific templates should be expanded in v0.4.12 and which negative contexts must remain blocked.

This is an offline evaluation only; no auto-promotion, no external source approval, no training, no changes to `chat.py` or `/sleep`.
