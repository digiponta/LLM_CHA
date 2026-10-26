# LLM_CHA v0.9.7.81 — Semantic Topic Isolation Validator

Audits session-only journal events for source/target provenance, transition continuity, transfer events carrying unrelated Quality, unexpected source/target fields on non-transfer events, cross-topic quality writes, and mismatches between independently maintained live focus and audited focus. Returns ISOLATED, VIOLATION, or INCOMPLETE.

Files:
- semantic_topic_isolation_v09781.py
- test_semantic_topic_isolation_v09781.py (six tests)
- chat.py outputs [semantic_topic_isolation=...]

```powershell
git fetch origin
git switch v0.9.7.81
git pull --ff-only
python -m unittest -v test_semantic_topic_isolation_v09781.py test_multitopic_replay_v09780.py test_cross_context_consistency_v09779.py test_semantic_state_consistency_v09778.py
python chat.py
```

Manual transcript:
1. 私は、スファレライトが好きです。
2. きらきらしてるところが心地よい
3. ところでダイヤモンドは？
4. ところでスファレライトは？

Expect ISOLATED with checked_events=4. This remains limited rule-based session validation; it does not assert universal natural language or distributed SKI safety. No Windows test execution has been run by the assistant.
