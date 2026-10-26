# LLM_CHA v0.9.7.65 — Japanese Causal Paraphrase Normalization

Experimental branch extending v0.9.7.64. This version adds a small, conservative query-only normalization layer before the existing source-literal causal retrieval, enabling variants including `なぜカットが難しいの？`, `どうしてカットが難しいの？`, and `カットが難しい理由は？`. Source text is never rewritten; returned evidence remains EXTERNAL_UNVERIFIED and is not promoted or trained.

Changes:
- `causal_question_normalization_v09765.py` — query normalization
- `chat.py` — normalize before causal retrieval and fallback intent detection
- `test_causal_question_normalization_v09765.py` — paraphrase regression

Windows verification:

```powershell
git fetch origin
git switch v0.9.7.65
git pull --ff-only
python -m unittest -v test_causal_question_normalization_v09765.py test_clipboard_causal_evidence_v09762.py test_causal_ellipsis_v09763.py
python chat_window_v061.py
```

Acceptance: search for スファレライト, copy the results, read the clipboard and ask `なぜカットが難しいの？`. Expect a quote of the labeled causal passage, route CLIPBOARD_CAUSAL_EVIDENCE. This remains a pattern-based normalization prototype, not general semantic entailment. Windows/GPU runtime is not yet validated.
