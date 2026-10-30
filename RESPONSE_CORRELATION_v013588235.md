# LLM_CHA v0.13.58.82.35 — Response Correlation

Observed on v0.13.58.82.34: one Evidence-conditioned attempt completed with REJECT_NOT_ENTAILED, fallback displayed, then an extra `AI: 未学習です` appeared.

Changes:
- GUI suppresses AI> lines with **no pending question** and records `[Uncorrelated AI suppressed]` in diagnostics.
- For paired Evidence responses, diagnostics show gate, candidate length, and a brief candidate preview (first 100 chars, session diagnostic only) to help understand why string-extract matching rejected.
- Add a standalone correlation policy plus four unit tests.

Caveat: this is a safety-net for **unpaired** outputs, not a wire-level request ID protocol. CLI protocol has no response IDs. A delayed line could still be incorrectly paired with a later queued question. Full per-turn framing and output count validation will require modifying chat.py / GUI transport together. Evidence comparison remains lexical and not a verified entailment model.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.35-response-correlation
python -m unittest -v test_response_correlation_v013588235.py test_prompt_normalization_v013588234.py
python chat_gui.py
```

Conversation: `宇宙とは` -> `CPU` -> `宇宙の話に戻って` -> `もう少し詳しく` -> `/genstats`. Check the GUI transcript for no extra orphan `AI: 未学習です` and diagnostic tab for `[Uncorrelated AI suppressed]` and `[Evidence Gate]`.
