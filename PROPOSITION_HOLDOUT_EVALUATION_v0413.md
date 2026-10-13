# LLM_CHA v0.4.13 — Frozen Distinct-Concept Proposition Evaluation

This phase freezes **30 new hand-authored examples** in `data/proposition_holdout_v0413.json` before producing the evaluation report, and runs both frozen v0.4.10 and v0.4.12 extractors unchanged. Examples cover multiple concepts (quantum physics, CPU, GPU, astronomy, music, cells, mathematics and others), negation, quotations, hypotheticals, hedging, reverse definitions, and multiple sentences.

**Methodological caveat:** This is a **post-development, hand-authored fixed test set**, not a statistically representative sample, not an independently collected Wikipedia corpus, not independent human annotation, and **not a true blind holdout**. The fixture is frozen in commit `a4793ea02e169377b057356fe78e31e6c1fdfed9`, and the resulting report includes its SHA256. Evaluate once and avoid silently tuning v0.4.12 to these examples. A future evaluation should use separately gathered and labeled article leads with independent reviewers.

Outputs include TP/FP/FN/TN, precision, recall, specificity, balanced accuracy, and per-case disagreements. Some labels are intentionally strict (e.g. descriptive properties vs taxonomic definitions, embedded hypotheticals), which can surface both parser limitations and labeling-boundary discussions. No mutation of Truth Gate, review state, Semantic Memory, corpus, `chat.py`, model weights or `/sleep`; extracted content remains UNVERIFIED and non-trainable.

## PowerShell verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_evaluate_proposition_holdout_v0413.py test_article_proposition_alignment_v0412.py
python evaluate_proposition_holdout_v0413.py --report results/proposition_holdout_v0413.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Do not mistake unit tests passing for extraction metric success. Examine discrepancies and use them to prioritize **future separately versioned** improvements without changing these labels.
