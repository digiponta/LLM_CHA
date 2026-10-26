# LLM_CHA v0.9.7.83

Introduces an in-process Semantic Dialogue transaction. It snapshots dialogue and topic state, applies a candidate update, validates integrity, and commits or rolls back. Four regression tests added in test_semantic_transaction_v09783.py. This does not provide persistent storage or model weight rollback. Windows validation is pending.

Run: python -m unittest -v test_semantic_transaction_v09783.py test_semantic_integrity_gate_v09782.py test_semantic_topic_isolation_v09781.py
