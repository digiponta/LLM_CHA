# LLM_CHA v0.9.7.78 — Semantic State Consistency Validator

Compares reconstructed Event Replay quality focus with independently maintained SemanticEventJournal.focus.

Results:
- CONSISTENT: compared focus matches and replay complete.
- MISMATCH: quality focus differs, or optional externally supplied active topic differs.
- INCOMPLETE: Replay history is missing/truncated or invalid.

Important scope: current chat.py calls validator without the optional runtime active topic, so runtime topic itself is NOT checked in the normal diagnostics; the status only covers live focus vs Replay focus. This is not a full comparison with every TopicContext or dialogue state field.

Files:
- semantic_state_consistency_v09778.py
- test_semantic_state_consistency_v09778.py (five tests)
- chat.py logs [semantic_consistency=...]

Windows:
```powershell
git fetch origin
git switch v0.9.7.78
git pull --ff-only
python -m unittest -v test_semantic_state_consistency_v09778.py test_semantic_event_replay_v09777.py test_clarification_provided_v09776.py test_semantic_event_journal_v09774.py
python chat.py
```

For the five-turn sphalerite scenario, expect [semantic_consistency={"status": "CONSISTENT", ..., "replay_complete": true, "replay_sequence": 5}] on the final event. Windows testing pending. No training, disk persistence or automatic promotion is performed.
