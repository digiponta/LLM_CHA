# LLM_CHA v0.7.1 — Approved / Candidate Memory Separation

This branch establishes a **separate experimental store** for pending and rejected
knowledge and an **approved-only store** for explicitly reviewed records.
Both are UTF-8 JSONL and preserve `source_id`.

## API

```python
from dual_semantic_memory_v071 import DualMemory
memory=DualMemory("data/approved_v071.jsonl","data/candidates_v071.jsonl")
id=memory.propose("猫とは","ネコは動物です。","human-review:1")
assert memory.lookup_approved("猫とは") is None
memory.approve(id)  # explicit human-controlled promotion
assert memory.lookup_approved("猫とは")["status"]=="APPROVED"
```

Alternative: `memory.reject(id)` keeps the candidate in REJECTED status.
Conflicting approved answers are blocked. Writes are atomic per individual
store, and the approved store is written before candidate removal to avoid
silently losing an approved record on interruption. True cross-file ACID
transactions, lifecycle audit history and multiclient locks are future tasks.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.1
python -m unittest -v test_dual_semantic_memory_v071.py
```

**Scope boundary**: No integration into `chat.py`, no migration of existing
Semantic Memory, no adapter training, no `/sleep`, no automatic approval.
The approved store is only a trusted *workflow state*; factual correctness
still depends on the human review process. v0.7.2 will add isolated
candidate-learning experiments.
