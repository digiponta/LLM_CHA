# LLM_CHA v0.2.35.0 — Adaptive Long-Term Context Management (prototype)

Branch: `v0.2.35-adaptive-context`, based on stable `v0.2.34`.

First phase of the post-release roadmap: a bounded, deterministic **topic retention policy**, distinct from Context Checkpoint, Semantic Memory and LLM weights.

`adaptive_context_v023350.py` provides:
- `observe(topic, pin=False)`: count accesses and update recency.
- `retention_order()`: deterministic pinned-first/recency ordering.
- Capacity-limited eviction of least recently used **unpinned** topics.
- Explicit `unpin` and `reset`.
- Fail closed when all topics are pinned, rather than silently dropping protected ones.

No automatic summarization, persistent writes, model learning, knowledge promotion, or Truth State modification. This is an **independent prototype** and is not connected to `chat.py` yet. Eviction or retention does not supersede v0.2.34 current-corpus/Truth Gate checks.

## Run

```powershell
git fetch origin
git switch --track origin/v0.2.35-adaptive-context
python -m unittest -v test_adaptive_context_v023350.py
```

Target: **10 tests**, pending local validation. Do not merge to `main` until existing regression and GPU gates also pass after integration.

## Next

Compare retention policies over long simulated conversations, add an opt-in adapter to `MultiTopicContext`, and define safety criteria for proposed context compression. Compression must not invent facts or replace authoritative Semantic Memory records.
