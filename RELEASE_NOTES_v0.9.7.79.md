# LLM_CHA v0.9.7.79 — Cross-Context Semantic Consistency

Experimental scoped consistency validator comparing:
- Independently maintained SemanticEventJournal.focus with Event Replay
- TopicContext.active_topic with Event Replay only after a dialogue-manager explicit topic switch

Semantic Memory is NOT_COMPARABLE to session-only USER_REPORTED dialogue claims, and is never modified. Pending clarification state is also marked not comparable because Event Replay does not reconstruct it.

Status:
- INCOMPLETE: missing/truncated event history
- MISMATCH: compared fields conflict
- CONSISTENT: compared Quality and explicit TopicContext match
- NOT_COMPARABLE: only Quality is comparable; no independently verifiable cross-context topic match

This is intentionally partial and does not claim full Dialogue Manager or Semantic Memory state equivalence.

Files: cross_context_consistency_v09779.py; test_cross_context_consistency_v09779.py (five tests), chat.py diagnostic [cross_context_consistency=...].

Windows:
```powershell
git fetch origin
git switch v0.9.7.79
git pull --ff-only
python -m unittest -v test_cross_context_consistency_v09779.py test_semantic_state_consistency_v09778.py test_semantic_event_replay_v09777.py
python chat.py
```

To test topic equality:
- ところでダイヤモンドは？ => expected cross_context_consistency.status CONSISTENT, compared contains topic_context.active_topic
- Ordinary preference-only scenario => NOT_COMPARABLE, because unrelated search TopicContext may not be semantically equal.

No Windows verification yet. Separate internalized=0/pending=56 checkpoint question remains open.
