# LLM_CHA v0.13.58.82.23 — Episodic Semantic Memory Integration (staging)

This release creates an explicit **approval-gated local episodic semantic memory store**, not automatic integration into the pre-existing trusted Nagato Semantic Memory or model weights.

## Architecture

Session EpisodeContext -> canonical JSON record (USER_SELF_REPORTED, PENDING) -> explicit approval -> local data/approved_episodic_memory.json (APPROVED).

Canonical record fields: schema, episode_id (UUID), topic, subject, action, observations (original_utterance, text, dimensions, semantic, provenance), provenance, approval, lifecycle, created_at.

No episode is saved merely by talking. The user must issue an explicit GUI command to approve a staged item. Wikipedia and clipboard data remain in a distinct EXTERNAL_UNVERIFIED evidence store and are not automatically included in the approved episodic store. Records are kept separate from trusted factual knowledge and LLM checkpoints. Approvals persist only to a local JSON file; no training, /sleep, vectorization, SKI export or cross-VM synchronization occurs here.

## Chat GUI commands

- `/episode stage` — snapshot current episode, display pending UUID, **not persisted**
- `/episode approve <UUID>` — explicitly approve and write only that record to the local JSON store
- `/episode reject <UUID>` — discard pending record
- `/episode list` — list approved records
- `/episode revoke <UUID>` — delete a locally approved record
- `/episode` — show help

Note: a staged item snapshots the episode at that moment. If more observations are added, stage a new snapshot before approval. To protect private self-reported experiences, do not commit the local JSON file into Git.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.23-episodic-semantic-memory
python -m unittest -v test_episodic_memory_gate_v013588223.py test_episodic_retrieval_v013588222.py test_episodic_context_v013588220.py
python chat_gui.py
```

Start a product experience dialogue, run `/episode stage`, verify the UUID, then `/episode approve <UUID>`. Test `/episode list` and `/episode revoke <UUID>`. Verify data/approved_episodic_memory.json never appears until explicit approval.

## Future next steps

Integrate the approved records with a separately scoped Semantic Memory read API, explicit identity/provenance constraints, deletion propagation and SKI compatibility. Approval is **not** automatic factual verification.
