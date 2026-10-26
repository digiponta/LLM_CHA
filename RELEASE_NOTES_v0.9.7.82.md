# v0.9.7.82 — Semantic Integrity Gate

Introduces a **pre-routing** integrity gate for the session-only Semantic Dialogue Manager.

* `semantic_integrity_gate_v09782.py`: evaluate journal topic isolation and cross-context consistency before invoking dialogue response handling.
* `chat.py`: if BLOCK, do not invoke the Semantic Dialogue Manager; display a guarded reply and diagnostic route SEMANTIC_INTEGRITY_BLOCK. Ordinary evidence handling is unchanged when the gate is not blocking.
* PARTIAL for preference-only contexts with no independent TopicContext comparison; ALLOW when an explicit topic-switch comparison is consistent; BLOCK for VIOLATION, MISMATCH or INCOMPLETE.
* `test_semantic_integrity_gate_v09782.py`: six tests including focus tampering, topic mismatch and truncated history.

Scope: preflight validates the existing state *before* the next utterance. Post-turn diagnostics are informational; this is not yet an atomic transaction that can roll back newly recorded invalid events. BLOCK currently emits a guarded response rather than falling through to the ordinary LLM, to avoid ungrounded use of a corrupted context. Existing clipboard evidence retrieval remains unchanged for non-blocked sessions.

Windows:
```powershell
git fetch origin
git switch v0.9.7.82
git pull --ff-only
python -m unittest -v test_semantic_integrity_gate_v09782.py test_semantic_topic_isolation_v09781.py test_multitopic_replay_v09780.py test_cross_context_consistency_v09779.py
python chat.py
```

Expected: after the normal four-turn preference/topic-switch sequence, `semantic_integrity_gate.status` is PARTIAL, PARTIAL, ALLOW, ALLOW. No local Windows test run by assistant.

Separate outstanding issue: Nagato Semantic Memory `internalized=0 / pending=56`, not addressed in this branch.
