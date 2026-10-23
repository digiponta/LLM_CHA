# LLM_CHA v0.7.40 — Approved Knowledge → Trusted Semantic Sleep

## Design

Reference-approved records in `data/approved_v071.jsonl` are mirrored
idempotently to the dedicated
`data/approved_semantic_memory_v0740.jsonl` ledger. Unlike the
legacy Nagato memory, this ledger is **not rebuilt from the raw corpus
at startup**, so reference approvals and source IDs are retained.

On `/sleep`, only these `APPROVED` records are queued in the existing
Trusted learning log as `reference-approved-semantic-sleep` pairs.
The existing trainer is invoked if new Approved pairs were queued,
even when the earlier Nagato Semantic Memory reports zero pending.
References to `PENDING` source evidence do not enter Trusted training.

The promoted operational approval is recorded independently of factual
verification; `truth_state=UNVERIFIED` remains in the ledger. No
Wikipedia extracts are used as training answers. The source/approval
ledger is distinct from legacy unified Semantic Memory to prevent
overwriting existing concepts.

## Commands

```powershell
git fetch origin
git switch --track origin/v0.7.40
python -m unittest -v test_approved_semantic_sleep_v0740.py test_approved_evidence_state_v0739.py test_evidence_reference_v0738.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat_window_v061.py
```

In the chat UI, run `/sleep` and inspect:

```text
[approved semantic sync: approved=N, synced=N, added=A, queued=Q]
```

When Q > 0 the Trusted online training pathway is reached. Whether
training succeeds and checkpoint-bound retention passes **must be
verified from the local GPU run**; staging is not proof of internalized
model knowledge.

Operational notes: the current dual-sleep command runs Experimental
Adapter sleep first. Failure there still aborts subsequent Trusted
training; this is not yet a transactional cross-model sleep.
Do not run concurrent writers against the same JSONL stores.
