# LLM_CHA v0.11.5 — bounded generation retry

When the live decoder's output fails the v0.11.4 quality gate, retry generation:
1. Beam-3, max_new_tokens = 2 × --max-tokens (96 by default)
2. Greedy, max_new_tokens = 3 × --max-tokens (144 by default)

The first VALID result is passed to Semantic Reconciliation. The result includes
retry_history with statuses. This uses the same checkpoint and tokenizer;
there is no learning, factual approval, automatic promotion, or /sleep.

If all attempts fail, return GENERATION_QUALITY_REVIEW. A damaged candidate is
not automatically offered for selection. Users can inspect retry_history and
choose to revise the prompt or supply validated evidence.

Tests:

```powershell
git pull --ff-only
python -m unittest -v test_semantic_reconciliation_v0110.py test_semantic_equivalence_router_v0111.py test_semantic_dialogue_bridge_v0112.py test_semantic_live_bridge_v0113.py test_generation_quality_gate_v0114.py test_generation_retry_v0115.py
$env:LLM_CHA_DECODE_MODEL = (Resolve-Path ".\model\model-gpu-v1.6.2-online.pt").Path
python semantic_live_bridge_v0113.py
```

Expected: 41 tests (previous 37 plus 4 new tests); final pass only
confirmed by running on the user's Windows environment.
