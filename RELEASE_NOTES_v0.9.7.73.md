# LLM_CHA v0.9.7.73 — Semantic Dialogue Transitions

Experimental follow-on from v0.9.7.72.

Changes:
- semantic_dialogue_transition_v09773.py: explicit rejection, correction and topic switch recognition
- semantic_dialogue_manager_v09772.py: routes recognized transitions, clears ephemeral context when interrupted
- chat.py: applies only explicit next_topic into TopicContext
- test_semantic_dialogue_transition_v09773.py: 5 parser tests
- test_semantic_dialogue_transition_integration_v09773.py: 4 manager tests

The correction is only accepted immediately following an explain_preference frame. Unrelated factual questions are not consumed. These user-reported dialogue states are not persisted, automatically promoted or used to train the model.

Windows test:

```powershell
git fetch origin
git switch v0.9.7.73
git pull --ff-only
python -m unittest -v test_semantic_dialogue_transition_v09773.py test_semantic_dialogue_transition_integration_v09773.py test_semantic_dialogue_manager_v09772.py
python chat.py
```

Note: This is bounded pattern matching, not general language understanding. No Windows validation performed.
