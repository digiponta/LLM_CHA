# LLM_CHA v0.11.4 — Generation Quality Gate

Standalone v0.11.3 CLI now checks generated text **before** semantic reconciliation.

- Empty or whitespace-only outputs continue to return GENERATION_UNAVAILABLE.
- MAX_TOKENS, replacement characters, control characters, and clear adjacent repetitions are flagged as GENERATION_QUALITY_REVIEW.
- Invalid outputs do **not** create clarification tickets and are not preferred automatically.
- Valid outputs proceed to existing comparison and Human-in-the-Loop reconciliation.

This stage does not automatically retry or correct a generated answer: it exposes a quality status for separate review. It is not a semantic-equivalence classifier. Valid outputs may still be incorrect, and the heuristics may miss subtle corruption.

Windows PowerShell:

```powershell
git pull --ff-only
python -m unittest -v test_semantic_reconciliation_v0110.py test_semantic_equivalence_router_v0111.py test_semantic_dialogue_bridge_v0112.py test_semantic_live_bridge_v0113.py test_generation_quality_gate_v0114.py
$env:LLM_CHA_DECODE_MODEL = (Resolve-Path ".\model\model-gpu-v1.6.2-online.pt").Path
python semantic_live_bridge_v0113.py
```

Expected total: 37 unit tests (previous 29 + new 8), subject to the user's local execution.
