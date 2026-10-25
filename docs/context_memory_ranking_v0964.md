# v0.9.6.4 — Article-aware Memory Evidence Ranking

This branch preserves unverified Nagato corpus excerpts but ranks them using
the selected Wikipedia article as a context hint.

- After `メモリとは` -> `1: 記憶装置`, `貴方はどう思う？` should
  refer to computer-memory corpus evidence rather than biological memory.
- `/cha-memory-subtopics` and `/cha-memory-eval` return context-ranked
  memory excerpts when a selected article is active. Without selection,
  document order is preserved.
- The selected article and requested concept remain distinct, and no
  Semantic Memory approval or model weights are modified.
- Classification is lexical, not a Semantic Vector model and not a factual
  entailment validator. The A/B candidate remains a deterministic template.

PowerShell:
```powershell
git fetch origin
git switch --track origin/v0.9.6.4
python -m unittest -v test_context_memory_ranking_v0964.py test_memory_subtopic_v0963.py test_wiki_selection_corpus_v0962.py test_grounded_generation_gate_v096.py
python chat.py
```
Runtime probe: `メモリとは`, `1`, `貴方はどう思う？`,
`/cha-memory-subtopics`, `/cha-memory-eval`.
