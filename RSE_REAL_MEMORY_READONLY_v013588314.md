# v0.13.58.83.14 — Real Semantic Memory read-only bridge

Existing chat.py config confirms these local stores:
- data/unified_semantic_memory_v1090.jsonl (concept/assistant/provenance)
- data/truth_state_v10103.jsonl (concept/state; default UNVERIFIED)
The memory's presence, training, or internalization is **not equivalent to approval**. This bridge requires explicit approved=true or approval_state=APPROVED **and** matching truth state TRUE for direct selection. Other entries stay unavailable; no automatic fallback to unverified facts.

This strict policy may mean no real stored records qualify. If so, inspect the project's actual approval workflow and metadata rather than treating the knowledge as missing. Matching currently requires the exact query `<concept>とは`, so more general queries may not match. Factual phrase "スファレライトの化学組成は？" does not automatically map to the concept "スファレライト" here.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.14-live-memory-readonly
python -m unittest -v test_rse_real_memory_readonly_v013588314.py test_rse_memory_theme_shadow_v013588313.py
python rse_real_memory_readonly_v013588314.py --query "閃亜鉛鉱とは"
python rse_real_memory_readonly_v013588314.py --query "少しお話ししませんか？"
```

Read-only; no chat.py modifications, no memory writes, no model training. A missing authoritative approval flag causes fail-closed, **not** a claim that the system lacks trained knowledge. The command is a shadow probe, not a production integration or verification of claimed facts.
