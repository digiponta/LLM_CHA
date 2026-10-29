# v0.13.58.82.8 — Legacy Dialogue Recovery (first bridge)

## Evidence from the old v0.9.7.45 screenshot
The previous GUI showed natural follow-ups for user experiences (e.g. 「黒耳を飲んだ」→ ask about flavor), and a semantic diagnostics header (Trusted internalized, pending, Last route). The historical `v0.9.7.45` branch was verified to exist. Its original GUI implementation has not yet been identified or migrated; `chat_window_v061.py` on that branch is a terminal mirror, not the pictured GUI.

## Implemented
- Conservative GUI social-intent bridge for explicit 「飲んだ」「食べた」「満足した」 and simple taste feedback; bypass malformed generative completions for these cases.
- Keeps a short list of previously quoted menu items; uses it to disambiguate 「黒耳」 when a quoted entry exists.
- Clears referenced products on a new search topic.
- Keeps existing evidence lookup, Google/Wiki/Clipboard tools, and original LLM for other queries.

## Still pending
- The genuine legacy semantic diagnostics GUI and multi-turn topic context must be located and ported; this version does not claim full v0.9.7.45 behavior.
- Experience replies are simple rules, not proof of LLM learning. Personal facts are not permanently saved.
- Broader conversational generalization and independent evaluation remain open.

## Verify on Windows
```powershell
git fetch origin
git switch v0.13.58.82.8-dialogue-recovery
python -m unittest -v test_social_dialogue_bridge_v01358828.py test_general_evidence_retrieval_v01358827.py
python chat_gui.py
```
Try: 「スターバックスをぐぐって」, clipboard read of menu, 「ドリンクの種類は」, 「黒耳を飲んだ」, 「酸味と甘みのバランスが良かった」, 「満足した」. Also ensure 「宇宙とは」 still uses the existing LLM runtime.
