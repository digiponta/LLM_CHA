# LLM_CHA v0.9.7.12 — Contextual Evidence Expansion

Adds source-preserving, heuristic heading expansion to explicitly requested
clipboard evidence questions. When a short matched heading is followed within
four nonempty lines by a substantial description (75+ characters), the response
includes that follow-on text as `RELATED_CONTEXT` rather than claiming its
semantic relationship is independently verified.

Existing menu-oriented QA and unrelated chat routes are unchanged.
No LLM generation, factual verification, automatic storage, or training.

```powershell
git fetch origin
git switch --track origin/v0.9.7.12
python -m unittest -v test_clipboard_context_expansion_v09712.py test_clipboard_generic_evidence_v09711.py test_clipboard_grounded_qa_v0977.py
python chat_window_v061.py
```

Copy the WIZG.org research page; press the clipboard GUI button; then ask
`このページでQuantum Hyper-Aetherについて記述は？`
and `このページでSemantic Operating Systemsについて記述は？`.

Limitation: neighboring text is context, not proof of relation. A heading
near unrelated navigation can produce misleading context; use human review
before any knowledge promotion.
