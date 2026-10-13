# LLM_CHA v0.4.28.11 — Generation–Gate Correlation

Branch `v0.4.0`. Adds `analyze_generation_gate_v042811.py`, a read-only analyzer for **v0.4.28.10 traced capture JSON**.

This tool reports each question, final answer, Gate resolution, pre-Gate primary text, probe candidates, and primary-vs-final exact match when the association is unambiguous. For 52 SINGLE groups, all group candidates belong to the single question. For four MULTI groups (12 turns), the current trace file has only group-level event ordinals, not turn IDs: the tool deliberately records `MULTITURN_UNRESOLVED`, preserves candidate count only at group level, and never assigns candidates to the wrong turn.

Even an exact primary/final match is not a quality score, semantic equivalence, proof of Gate correctness, or causal attribution. Canonical retrieval may legitimately yield zero model-generation events. Retrieval candidates are not instrumented. All causal attribution remains `UNDETERMINED`.

## Windows instructions

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v `
  test_analyze_generation_gate_v042811.py `
  test_isolated_stage_trace_v042810.py `
  test_runtime_stage_observability_v04289.py `
  test_diagnose_pipeline_attribution_v04288.py `
  test_diagnose_false_accept_v04287.py `
  test_eval_quality_v04286.py `
  test_capture_chat_benchmark_v04283.py `
  test_prepare_chat_benchmark_v04282.py `
  test_persona_response_shadow_v0421.py

python analyze_generation_gate_v042811.py `
  --capture results/chat_benchmark_capture_trace_v042810.json `
  --output results/generation_gate_analysis_v042811.json
```

Expected 56 tests (previously 51 + 5 synthetic structural tests). Preserve the input. Output is new-only, includes source SHA-256, and retains raw generation strings; review for sensitive content before sharing. This is a developmental test set, not an independent holdout. No changes to chat.py, model weights, Truth Gate semantics, Semantic Memory, /sleep or /train.

Suggested next step: inspect candidate text and agreement for specific ACCEPT cases, and design turn-ID stamped traces and read-only retrieval instrumentation. Avoid threshold adjustments based solely on this benchmark.
