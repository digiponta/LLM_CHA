# LLM_CHA v0.4.28.5 — Capture Diagnostic Separation

Branch: `v0.4.0`. `capture_chat_benchmark_v04283.py` keeps existing CLI. This revision separates child process execution, captured answers, and character-quality warnings.

- `failure_category`: `TRANSPORT_ENCODING_ERROR` (actual Python encoding/decoding or tokenizer input exception), `TIMEOUT`, `RUNTIME_ERROR`, or `NO_ANSWER`.
- `diagnostic_warnings`: `REPLACEMENT_CHARACTER_DETECTED` when U+FFFD appears anywhere in the transcript; `ANSWER_REPLACEMENT_CHARACTER` when it appears in extracted answer.
- `all_answers_captured`: whether each expected turn has a recognized answer.
- U+FFFD alone no longer changes `FINISHED` to `CAPTURE_FAILED`; no claim is made that the model output is fluent/correct.
- Preflight still stops after the first process-level/capture failure. Original checkpoint is SHA-256 checked before/after execution.

Run:
```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_capture_chat_benchmark_v04283.py test_prepare_chat_benchmark_v04282.py test_persona_response_shadow_v0421.py
python capture_chat_benchmark_v04283.py --run --manifest results/chat_benchmark_manifest_v04282.json --checkpoint model/model-gpu-v1.6.2-online.pt --tokenizer model/tokenizer-v0.7-bpe.json --output results/chat_benchmark_capture_v04285.json --timeout-per-group 240
```

The previous capture reports must not be overwritten. This is development evaluation, not an independent holdout. The temporary working copy is not a full filesystem/network sandbox; reports may contain sensitive input and must be reviewed before publishing. No changes to `chat.py`, Truth Gate, Semantic Memory or `/sleep`.
