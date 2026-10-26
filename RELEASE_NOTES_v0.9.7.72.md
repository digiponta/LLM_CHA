# v0.9.7.72 — Semantic Dialogue Manager (experimental)

Unifies the previously separate preference, reason, and short-agreement routing into one session-only manager, without modifying evidence retrieval or model weights.

Files:
- semantic_dialogue_manager_v09772.py: SemanticDialogueManager and DialogueResult
- chat.py: one shared manager call for GUI and CLI
- test_semantic_dialogue_manager_v09772.py: five focused unit tests

Expected full dialogue:
- 私は、スファレライトが好きです。 -> TOPIC_PREFERENCE_ACK / express_preference
- きらきらしてるところが心地よい -> TOPIC_PREFERENCE_ACK / explain_preference
- そうだよ -> SEMANTIC_DIALOGUE_AGREEMENT

Evidence questions (e.g. 屈折率は？) are not handled by the manager and continue to Clipboard Attribute or Causal Evidence Retrieval. Unrelated questions terminate the temporary preference follow-up context. Frames remain USER_REPORTED and are not persisted, trained, or auto-approved.

Windows:
```powershell
git fetch origin
git switch v0.9.7.72
git pull --ff-only
python -m unittest -v test_semantic_dialogue_manager_v09772.py test_dialogue_agreement_v09771.py test_semantic_dialogue_state_v09770.py test_causal_question_normalization_v09765.py
python chat.py
```

This is a consolidation of constrained rule-based conversation logic, not yet a general Semantic Dialogue Manager supporting contradiction/correction or arbitrary paraphrases. Windows runtime validation is pending. Memory checkpoint integrity remains a separate unfinished item.
