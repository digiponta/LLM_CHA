# LLM_CHA v0.4.28.16 — Generation vs. Gate Review Packet

Read-only focused diagnostic. Consumes the previously generated `results/gate_review_queue_v042815_2.json` and produces four cases, A04, A05, C05 and C07, with input question, final answer, recorded Gate resolution/semantic agreement, primary text, and observed generation candidates. This is evidence for manual review, not an automated classifier. Human labels are only included if present. Candidate relevance stays NOT_LABELED, retrieval stays NOT_OBSERVED, and causal attribution stays UNDETERMINED.

On Windows PowerShell:

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile inspect_generation_gate_v042816.py
python -m unittest -v `
  test_inspect_generation_gate_v042816.py `
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

python inspect_generation_gate_v042816.py `
  --queue results/gate_review_queue_v042815_2.json `
  --output results/generation_gate_review_v042816.json
```

Expected 81 tests (76 preceding + 5 new), pending local verification. The output is new-only (no overwrite). Upload the output report to inspect actual candidate texts and propose manual evidence labels. No changes to model weights, chat.py, Truth Gate, /sleep or Semantic Memory; no modifications to other branches.
