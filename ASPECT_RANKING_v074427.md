# LLM_CHA v0.7.44.27 — Aspect Relevance Ranking Baseline

The `expanded_aspect` retrieval path now scores eligible sentences from
the same Wikipedia article instead of accepting the first keyword hit.
Aspect-weighted lexemes, explanatory phrasing and generic-intro penalties
provide a deterministic **lexical ranking baseline**. This is *not*
semantic embedding similarity or BM25. It makes no factual predictions.

This build retains the prior evidence-length/missing-math gate, requires
a Wikipedia article URL, preserves EXTERNAL_UNVERIFIED, train_ready=False,
and auto_promote=False. On source-fetch error it falls back to the
existing excerpt rather than hallucinating further text.

## Verify

```powershell
git pull
python -m unittest -v test_aspect_relevance_v074427.py test_aspect_ranking_runtime_v074427.py test_wiki_expanded_aspect_v074426.py test_aspect_evidence_v074425.py test_aspect_runtime_v074425.py
python chat_gui_v07447.py
```

Conversation test: `量子力学とは` → `もっと詳しく` twice →
`基本原理` → `数式` → `実験` → `応用`.
Evaluate retrieval relevance separately from truth. Future work should
measure baseline top-1 precision against a labeled holdout set and
then add BM25/semantic-vector comparisons.
