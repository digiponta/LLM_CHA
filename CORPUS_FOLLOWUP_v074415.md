# v0.7.44.15 — Guarded Corpus Follow-up

The GUI enables the opt-in `LLM_CHA_CORPUS_FOLLOWUP=1` mode.
After a UNVERIFIED CORPUS_MEMORY retrieval, an immediately following
`もっと詳しく` / `もう少し詳しく` no longer falls into unrestricted
generation. Instead it explains that the displayed source is unverified,
no additional evidence has been provided, and requests the user's desired
verification target. It neither invents a new physical claim nor promotes
the source to Trusted. The context expires after the follow-up or a
different utterance.

This is intentionally not new evidence expansion. A separate
source-backed cursor with proposition-level provenance is needed before
a richer explanation can be delivered.

```powershell
git pull
python -m unittest -v test_corpus_followup_v074415.py test_corpus_followup_wiring_v074415.py
python chat_gui_v07447.py
```

Manual conversation: `宇宙とは` → `もう少し詳しく` → `GPUとは`.
Confirm the middle answer is a clear unverified-context clarification,
not `未学習です`, and the last answer is unaffected.
