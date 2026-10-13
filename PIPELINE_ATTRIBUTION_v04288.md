# LLM_CHA v0.4.28.8 — Answer Relevance & Gate Attribution (Evidence-Limited)

**Branch:** `v0.4.0`. New read-only command: `diagnose_pipeline_attribution_v04288.py`.

This version **does not assert root cause** from output text alone. It aligns the 64-turn quality triage against an optional original capture JSON, extracts verbatim recorded gate reasons and gate decisions, and labels retrieval, generation, and gate **causal attribution** `UNDETERMINED` until stage-level evidence is available. A bad accepted final answer demonstrates a bad outcome, but cannot alone identify whether retrieval, generation or gate is primarily responsible.

It leaves review fields for a human and lists required instrumentation (retrieval candidates/scores, pre-gate raw generation, gate inputs/thresholds). If the original capture is provided, all 64 question/answer pairs must match before a report is written. SHA-256 hashes bind output to sources. No model invocation or writes to Semantic Memory, /sleep, Truth Gate or chat.py.

## Windows commands

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v `
  test_diagnose_pipeline_attribution_v04288.py `
  test_diagnose_false_accept_v04287.py `
  test_eval_quality_v04286.py `
  test_capture_chat_benchmark_v04283.py `
  test_prepare_chat_benchmark_v04282.py `
  test_persona_response_shadow_v0421.py

python diagnose_pipeline_attribution_v04288.py `
  --triage results/chat_quality_triage_v04286.json `
  --capture results/chat_benchmark_capture_v04284.json `
  --output results/pipeline_attribution_v04288.json
```

The original v04284 capture retains its historic CAPTURE_FAILED flags for two responses; these do not by themselves imply missing answers. Development-only benchmark, not independent holdout. Do not train on these test prompts. This revision intentionally does not collect new live internal stage telemetry: that would require separate opt-in runtime instrumentation design and review.
