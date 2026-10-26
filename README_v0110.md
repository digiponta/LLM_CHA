# LLM_CHA v0.11.0 — Interactive Semantic Reconciliation (experimental)

This branch is based on v0.10.1-semantic-decoding and adds a standalone
human-in-the-loop clarification store. It **does not** automatically infer
semantic equivalence, replace runtime answers, approve knowledge, or trigger /sleep.

Workflow: open a ticket for a DIVERGENT or UNKNOWN pair; present A/B to the user;
record prefer_a / prefer_b / both_contextual / neither. Both-contextual requires
a distinguishing context. Reviews are immutable and preserve both candidate
expressions and available provenance. The preference remains USER_REVIEWED with
factual_truth=UNVERIFIED and approval_state=NOT_APPROVED.

Run tests:

```powershell
python -m unittest -v test_semantic_reconciliation_v0110.py
```

Example:

```python
from semantic_reconciliation_v0110 import ReconciliationStore, render_question
store = ReconciliationStore()
ticket = store.open("物質波とは", "物質波はドブロイ波である", "物質波は電磁波である")
print(render_question(ticket))
reviewed = store.review(ticket["id"], "prefer_a")
print(reviewed["preferred_expression"], reviewed["approval_state"])
```

Future steps: integrate ticket creation into dialogue runtime only when an
independent semantic comparison returns a reliable conflict; add stable
evidence identifiers, concurrency-safe review, approval policy, and holdout
evaluation. Do not confuse user preference with objective factual validation.
