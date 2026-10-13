# LLM_CHA v0.4.28.15 — Evidence-Based Human Review Queue

This read-only tool joins the earlier **generation–Gate analysis** with **Gate/relevance comparison** and creates a prioritized review queue containing question, final answer, generation candidates, the observed Semantic Agreement score, and any explicit human label. It does **not** automatically label bad answers. A04/A05/C05/C07 are preselected developmental review examples, not proven failures.

Priority: (1) explicitly human-labeled ACCEPT/relevance conflicts; (2) unreviewed focus cases; (3) other unreviewed ACCEPTs; (4) remaining cases. Multiturn unresolved events are never reassigned. All root causes remain UNDETERMINED.

## Windows commands

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v `
  test_prepare_gate_review_queue_v042815.py `
  test_compare_gate_relevance_v042814.py `
  test_review_semantic_relevance_v042813.py `
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

python prepare_gate_review_queue_v042815.py `
  --analysis results/generation_gate_analysis_v042811.json `
  --comparison results/gate_relevance_comparison_v042814.json `
  --output results/gate_review_queue_v042815.json
```

Expected 76 unit tests (71 prior + 5 new). Reports must be from the same capture; the tool aligns by ID, turn and Gate resolution, but **does not currently cross-check question/answer content against the comparison** because that report omits those values. Source SHA-256 hashes are included. Human labels currently total zero, so the queue is for review preparation rather than a measured False ACCEPT rate. To create nonzero labels, edit the existing v042813 CSV and regenerate v042814 comparison under a new output path.

No training, no changes to chat.py, Truth Gate, Semantic Memory, /sleep, main or model parameters.
