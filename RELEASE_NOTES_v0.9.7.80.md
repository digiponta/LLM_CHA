# LLM_CHA v0.9.7.80 — Topic Transfer and Replayable Clarification

Experimental event-schema extension on top of v0.9.7.79.

- Topic-switch events now record `source_topic` and `target_topic` separately, with `previous_quality=null`. The legacy `topic` field remains the destination for compatibility.
- Event Replay reconstructs `awaiting_clarification` after rejection and `awaiting_new_reason` after acknowledgement; replacement reasons clear both.
- Interruptions that cancel an outstanding clarification produce `clarification_cancelled` so the replay doesn't incorrectly report a pending state.
- Cross-context validator compares reconstructed wait flags against the live Dialogue Manager. It continues to return NOT_COMPARABLE when no explicit topic switch establishes independent TopicContext comparability, and excludes Semantic Memory from the comparison.
- test_multitopic_replay_v09780.py adds five regression tests.

Windows:
```powershell
git fetch origin
git switch v0.9.7.80
git pull --ff-only
python -m unittest -v test_multitopic_replay_v09780.py test_cross_context_consistency_v09779.py test_semantic_state_consistency_v09778.py test_semantic_event_replay_v09777.py test_clarification_provided_v09776.py test_clarification_v09775.py test_semantic_event_journal_v09774.py test_semantic_dialogue_transition_integration_v09773.py
python chat.py
```

Note that a partially truncated 64-event journal produces INCOMPLETE; this is a session-only event protocol, not a persistent checkpoint. Windows runtime verification pending.
