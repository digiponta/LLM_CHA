# LLM_CHA v0.4.28.14 — Gate Agreement vs. Human Relevance

This **read-only** command joins (a) the 64-turn v0.4.28.12 validation, (b) the v0.4.28.10 traced capture, and (c) the v0.4.28.13 manual-review CSV by **group ID + turn index**. The join validates source question and final answer, and the CSV is independently validated against immutable fields. Only explicit human labels are compared with recorded Gate `sem_agreement`; missing scores and unreviewed answers are excluded from paired counts. High semantic agreement is not treated as proof of answer relevance; results do not imply root-cause attribution, model correctness or independent benchmark quality.

## Windows commands

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v `
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

python compare_gate_relevance_v042814.py `
  --validation results/semantic_probe_validation_v042812.json `
  --capture results/chat_benchmark_capture_trace_v042810.json `
  --reviews results/semantic_relevance_review_v042813.csv `
  --output results/gate_relevance_comparison_v042814.json
```

Expected 71 tests (66 previous plus five new). Input must be the **traced** capture aligned with the validation file. The report is new-only and includes input hashes. The comparison runs without a GPU; the review CSV may be entirely blank but then zero human-reviewed cases will be reported. This is not a substitute for manual evaluation.

The tool does not modify `chat.py`, Semantic Memory, Truth Gate thresholds, /sleep, or model weights. No main branch changes.
