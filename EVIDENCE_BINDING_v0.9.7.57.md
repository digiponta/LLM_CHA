# v0.9.7.57 — Clipboard Evidence Binding (experimental)

This branch adds a **standalone** evidence binder and 8 scoped tests.
It is NOT yet wired to chat.py's clipboard ingestion / TopicContext dispatcher.

## Windows verification

```powershell
git fetch origin
git switch v0.9.7.57
python -m unittest -v test_clipboard_evidence_binding_v09757.py
```

## Proposed runtime wiring (not yet applied)

1. Create one `ClipboardEvidenceSession()` for each chat session.
2. When the existing Google clipboard ingestion succeeds, call
   `session.ingest(clipboard_text, subject=resolved_topic_subject)`.
3. On every user follow-up, only after TopicContext resolves its subject,
   call `answer = session.answer(user_input, resolved_subject=resolved_subject)`.
4. If an answer exists, return `answer.render()` via the evidence-backed
   response route **before** unknown fallback. Keep the external/unverified label.
5. On `/reset`, call `session.clear()`. Clear it on unrelated clipboard content,
   session termination, subject changes or source expiration, as appropriate.

Do not enqueue this information for approval, memory promotion, or sleep training.
Other minerals/compositions are outside the current narrow regression fixture.
Prompt-injection handling, extraction across HTML fragments, source-URL capture,
contradiction analysis, TTL, and full GPU end-to-end tests remain future work.

## Acceptance transcript

- Clipboard: `スファレライトは化学組成が硫化亜鉛（ZnS）の鉱物である。`
- User: `スファレライトの成分は`
- Expected: `スファレライトの化学組成は硫化亜鉛（ZnS）です。［根拠：クリップボード由来・未検証］`
- User: `化学組成を知りたい` (TopicContext retains subject)
- Expected: same sourced answer.
