# LLM_CHA v0.9.7.62 — Noisy Search-Result Causal Retrieval Fix

Fixes the observed case where a copied Google result contains both a labeled causal statement and duplicate compatible snippets, but the v0.9.7.60 extractor returns no evidence.

- Prefer a unique labeled causal passage over duplicate search snippets.
- Fail closed on conflicting/ambiguous labeled passages.
- Save Google search subject into the per-conversation TopicContext.
- Maintain source_needed behavior if no unique evidence exists.
- Both GUI and CLI share chat.py.
- No evidence approval or training.

Verification (Windows):

```powershell
git fetch origin
git switch v0.9.7.62
git pull --ff-only
python -m unittest -v test_clipboard_causal_evidence_v09762.py test_clipboard_attribute_retrieval_v09759.py test_gui_clipboard_v09758.py
python chat_window_v061.py
```

Then search スファレライト, copy the results and click the GUI clipboard-reading control, ask なぜカットが難しいの？ without any prior attribute question. Expected: quote from the labeled 脆さとカットの難しさ passage, route CLIPBOARD_CAUSAL_EVIDENCE. This is an observed-scenario regression target, not a claim of independent factual verification.
