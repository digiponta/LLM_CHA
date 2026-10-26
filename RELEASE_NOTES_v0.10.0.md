# LLM_CHA v0.10.0 — Semantic Transaction Fault Injection

This branch carries forward v0.9.7.83 and adds `test_semantic_transaction_fault_v0100.py` with five deterministic fault-injection tests:

- Invalid topic transfer provenance must ROLLBACK.
- Cross-topic Quality write must ROLLBACK.
- Corrupted live Quality focus must ROLLBACK.
- Exception after journal/clarification mutation must ROLLBACK.
- A valid topic switch must COMMIT after a failed transaction.

Each failure test checks that the journal sequence and records, Quality focus, TopicContext, and clarification flags return to their pre-transaction snapshot.

Run on Windows:

```powershell
git fetch origin
git switch v0.10.0
git pull --ff-only
python -m unittest -v test_semantic_transaction_fault_v0100.py test_semantic_transaction_v09783.py test_semantic_integrity_gate_v09782.py test_semantic_topic_isolation_v09781.py test_multitopic_replay_v09780.py
```

This tests in-process atomicity only. Database writes, external side effects and model weights are not rolled back. Windows verification is pending. The Semantic Memory `internalized=0 / pending=56` issue remains a separate investigation.
