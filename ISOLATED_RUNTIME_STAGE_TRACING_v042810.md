# LLM_CHA v0.4.28.10 — Opt-in Isolated Runtime Generation Tracing

Branch: `v0.4.0`.

This release adds **opt-in pre-Gate generation tracing** to the existing isolated 56-group/64-input benchmark. `trace_chat_runtime_v042810.py` wraps `chat.generate_reply` at process startup and forwards every call and return value unchanged; the regular `chat.py` source is NOT modified. For each generation probe it records the actual generated text, seed, temperature, token count, model confidence and top-two margin in a JSONL file **inside the temporary staged project**. The capture runner copies these events into the newly generated JSON report.

- This is actual observation of generation candidates before the acceptance gate; it is not a proof of whether the response is right.
- `stage_trace.generation_candidates` is ordered for the **whole group** (including all three turns in a MULTI group); the ordinal is NOT a turn number. `seed=0` marks primary generation; other seeds mark probes. Some routes bypass generation entirely; they legitimately have empty candidate lists.
- `retrieval_status=NOT_OBSERVED`: actual retrieval candidate IDs and scores are **not yet instrumented**. Gate decisions remain available in the captured transcript; a future attribution analysis must correlate per-turn events carefully.
- Tracing is **off by default**. All model checkpoint/unknown gating settings are unchanged; `--no-learn` remains enabled; no /sleep, /train, Truth Gate or Semantic Memory code edits.
- The temporary project is **not a complete filesystem or network sandbox**, and the report contains potentially sensitive raw generation strings; inspect locally before sharing.
- Original benchmark is developmental and NOT an independent holdout.

## Pull and test

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v `
  test_isolated_stage_trace_v042810.py `
  test_runtime_stage_observability_v04289.py `
  test_diagnose_pipeline_attribution_v04288.py `
  test_diagnose_false_accept_v04287.py `
  test_eval_quality_v04286.py `
  test_capture_chat_benchmark_v04283.py `
  test_prepare_chat_benchmark_v04282.py `
  test_persona_response_shadow_v0421.py
```

## Opt-in traced GPU run (new destination)

```powershell
python capture_chat_benchmark_v04283.py `
  --run --trace-stages `
  --manifest results/chat_benchmark_manifest_v04282.json `
  --checkpoint model/model-gpu-v1.6.2-online.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output results/chat_benchmark_capture_trace_v042810.json `
  --timeout-per-group 240
```

Never overwrite v04284/v04285 capture data. Expected test count is 51 (previously 46 plus 5 new), pending verification on user's system. Do not treat an empty trace for a canonical retrieval route as an error.

Next step: inspect candidate strings for A04/A05/C05/C07 and compare actual candidates and Gate decisions, then design similarly read-only retrieval instrumentation. Do not adjust acceptance thresholds from these dev cases alone.
