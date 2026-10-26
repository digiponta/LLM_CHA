# LLM_CHA v0.9.7.58 — Topic Clipboard Evidence Priority

Experimental branch from v0.9.7.57. Changes:
- chat.py checks temporary clipboard evidence after TopicContext has resolved a subject, before returning SOURCE_NEEDED.
- topic_clipboard_bridge_v09758.py adapts the v0.9.7.57 evidence binder.
- test_topic_clipboard_bridge_v09758.py contains six scoped regression cases.

No source auto-approval, persistence, or /sleep training. Extracted content stays EXTERNAL_UNVERIFIED.
The copied text must already reside in clipboard_context.text. The standard /read-clipboard path sets this variable, but automatic clipboard ingestion in locally modified runtimes must be checked independently.

Run:
```powershell
git fetch origin
git switch v0.9.7.58
git pull --ff-only
python -m unittest -v test_clipboard_evidence_binding_v09757.py test_topic_clipboard_bridge_v09758.py
python chat.py
```

Acceptance: with clipboard content including a same-sentence reference to スファレライト and 化学組成が硫化亜鉛（ZnS）, both 'スファレライトの成分は' and '化学組成を知りたい' (after topic initialization) should route TOPIC_CLIPBOARD_EVIDENCE when final_guard_enabled is active.

Limitations: This is not yet validated in the target Windows/GPU runtime. The binder is deliberately strict; complicated page formatting may need separate extraction handling.
