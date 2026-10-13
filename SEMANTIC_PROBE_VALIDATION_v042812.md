# LLM_CHA v0.4.28.12 — Semantic Probe Agreement Validation

Branch: `v0.4.0`. New read-only `validate_semantic_probes_v042812.py`, taking the 64-turn output of `analyze_generation_gate_v042811.py`.

This analysis **separates** (1) candidate-to-candidate literal agreement, (2) candidate/question semantic relevance, and (3) final Gate decision quality. Only (1) is automatically measured, using whitespace-normalized **exact identity**, not embedding cosine or true semantic similarity. Axes (2) and (3) remain `NOT_EVALUATED` with blank human review fields. Do not interpret probe identity as agreement on truth or answer correctness. No automatic model-quality pass rate is produced.

The tool respects prior trace alignment: 52 SINGLE groups can be compared, while 12 turns from four MULTI groups remain `MULTITURN_UNRESOLVED`. Cases that did not run generation are unevaluable. No invented retrieval or root-cause attribution.

## Windows instructions

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v `
  test_validate_semantic_probes_v042812.py `
  test_analyze_generation_gate_v042811.py `
  test_isolated_stage_trace_v042810.py `
  test_runtime_stage_observability_v04289.py `
  test_diagnose_pipeline_attribution_v04288.py `
  test_diagnose_false_accept_v04287.py `
  test_eval_quality_v04286.py `
  test_capture_chat_benchmark_v04283.py `
  test_prepare_chat_benchmark_v04282.py `
  test_persona_response_shadow_v0421.py

python validate_semantic_probes_v042812.py `
  --analysis results/generation_gate_analysis_v042811.json `
  --output results/semantic_probe_validation_v042812.json
```

Expected 61 tests (56 previous, five added). This uses prior captured data; no GPU execution required. Output contains generated text and source SHA-256, so review before sharing. The benchmark is development-only, not an independent held-out estimate. No changes to weights, Truth Gate thresholds, memory, /sleep, /train or chat.py.

Next: manually review A04, A05, C05 and C07 with their candidate texts; acquire per-turn events and retrieval provenance before attempting causal attribution or changing the Gate.
