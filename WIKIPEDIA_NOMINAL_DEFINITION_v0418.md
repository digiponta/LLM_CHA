# v0.4.18 — conservative nominal-ending Wikipedia definition coverage

The v0.4.17 diagnostic for `化学とは` established that the Wikipedia article was retrieved but zero definitions were extracted. The opening Japanese Wikipedia sentence is a noun-ending definition, with an explicit `とは` marker and a terminal category noun, without the copula `である` (checked in the public article; local MediaWiki extract may differ).

A standalone `article_proposition_alignment_v0418.py` implements a **narrow** fallback ONLY after the unchanged v0.4.12 aligner produces zero candidates. It recognizes topic-exact `とは` (including parenthesized alternate names) and a small allowlist of nominal class/category endings. It preserves exact source spans, SHA validation through v0.4.12 and `UNVERIFIED`, `PENDING_REVIEW`, `eligible_for_training=False`. Quoted, negative, attributed, hypothetical and property-like examples remain excluded. `wikipedia_retrieval_diagnostics_v0417.py` now attempts this guarded fallback after `NO_DEFINITION`.

This is not an independent holdout or a general Japanese parser, and does not modify the frozen v0.4.13 labels, the older v0.4.12 implementation, Truth Gate, Semantic Memory, protected corpus, persona or model. No automatic Wikipedia learning.

## Verify (PowerShell)

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_article_proposition_alignment_v0418.py test_wikipedia_retrieval_diagnostics_v0417.py test_unknown_wikipedia_fallback_v0416.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

In chat try `化学とは`, `小説とは`, `哲学とは`. For `化学とは`, expect `[wiki-lookup=HIT]` if the live MediaWiki lead contains the supported nominal pattern. Otherwise diagnostics still show `NO_DEFINITION`. Live evaluation remains required before declaring success.
