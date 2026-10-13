# LLM_CHA v0.4.28.9 — Runtime Stage Observability Baseline

Branch `v0.4.0`. This is a **read-only stage-evidence extraction**, not yet live internal runtime instrumentation. It parses Gate metrics (confidence, agreement, semantic agreement, margin and thresholds when present) from the existing v04284 benchmark capture. It explicitly marks retrieval candidate IDs/scores and pre-gate raw generation as `NOT_OBSERVED`; it does not infer them from the final response. Every causal attribution remains `UNDETERMINED`.

## Windows validation

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v `
  test_runtime_stage_observability_v04289.py `
  test_diagnose_pipeline_attribution_v04288.py `
  test_diagnose_false_accept_v04287.py `
  test_eval_quality_v04286.py `
  test_capture_chat_benchmark_v04283.py `
  test_prepare_chat_benchmark_v04282.py `
  test_persona_response_shadow_v0421.py

python runtime_stage_observability_v04289.py `
  --capture results/chat_benchmark_capture_v04284.json `
  --output results/runtime_stage_observability_v04289.json
```

Expected 46 tests (41 existing + 5 new), but verify on the user's Windows machine. The existing capture is development-only. Captured gate log fields are observations, not evidence of their causal correctness. To acquire actual retrieval candidates and raw pre-Gate generation a **subsequent opt-in isolated trace instrumentation update** is required. This release does not alter chat.py, model weights, Truth Gate, memory, /sleep or /train.
