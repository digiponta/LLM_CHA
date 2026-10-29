# LLM_CHA v0.13.58.82.10 — Preference & Impression Dialogue Context

Adds a session-scoped preference bridge in the GUI before the legacy LLM fallback. Matches explicit statements such as:
- 「私は、スファレライトが好きです。」 → asks about its appeal
- 「きらきらしてるところが心地よい」 → acknowledges sparkle
- 「黄色が好きです」 → resolves the preferred color against the current topic

The active topic is set by the existing natural language search commands and is not persisted. Preference entries are kept in RAM only, separate from externally unverified Evidence, Semantic Memory, and model weights. Unmatched utterances continue through existing social replies or LLM inference. This is a narrow rule-based bridge, not full general-purpose preference understanding or a reconstruction of the old v0.9.7.45 GUI.

## Windows validation
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.10-preference-dialogue
python -m unittest -v test_preference_dialogue_v013588210.py test_causal_evidence_retrieval_v01358829.py test_social_dialogue_bridge_v01358828.py
python chat_gui.py
```
Then test 「スファレライトをぐぐって」, 「私は、スファレライトが好きです。」, 「きらきらしてるところが心地よい」, 「黄色が好きです」, and ensure causal questions and identity answers remain unchanged.
