# LLM_CHA v0.4.12 — Negation Guard & Definition Pattern Expansion

This release adds `article_proposition_alignment_v0412.py` as a **separate** guarded, rule-based definition alignment experiment. It imports the unchanged v0.4.10 extractor for integrity, schema and safety validation, then applies its own extraction and rejects explicit negative, question, quotation, hypothetical, uncertain, and mismatched-subject contexts. It supports `XはYである`, `XとはYである`, `XはYです`, `XはYを指す`, `XはYを意味する`, `XはYの一つ` and a narrow reverse form `YがXである`. Every candidate retains a literal source span, `UNVERIFIED`, and `PENDING_REVIEW`.

`compare_proposition_alignment_v0412.py` evaluates the original 20 v0.4.11 hand-authored examples and 12 further **development-time adversarial examples** against both frozen baseline and expanded version, reporting confusion matrix/precision/recall. These are not independent generalization evidence. Please inspect *all* FP cases before deploying. Negative and hypothetical guards are heuristic and not a full Japanese scope/negation analyzer.

No change to `chat.py`, Truth Gate, Semantic Memory, reviewer store, `/sleep`, model weights, or training; zero promotions.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_article_proposition_alignment_v0412.py test_article_proposition_alignment_v0410.py test_evaluate_japanese_proposition_v0411.py
python compare_proposition_alignment_v0412.py --report results/proposition_alignment_comparison_v0412.json
python article_proposition_alignment_v0412.py --evidence results/wikipedia_article_evidence_v0409_novel.json --report results/article_proposition_alignment_v0412_novel.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

**Note:** The code is newly committed, but test results, performance gains and GPU compatibility need local verification. Next build a genuinely independent, pre-registered held-out set with diverse concepts, negative scope and quotations before declaring generalization.
