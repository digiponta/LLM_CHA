# LLM_CHA v0.4.28.4 — Windows UTF-8 Benchmark Hardening

Branch: `v0.4.0`. The opt-in benchmark runner (`capture_chat_benchmark_v04283.py`) now starts each isolated child Python process with `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`, and decodes subprocess output using strict UTF-8. This addresses the mojibake and `TextInputSequence must be str` exceptions in the user's first full capture.

If the first benchmark case fails to complete or lacks a captured answer, remaining cases are skipped. A JSON failure report is still written under a **new** output filename. Report failures distinguish `ENCODING_ERROR`, `TIMEOUT`, `RUNTIME_ERROR`, and `NO_ANSWER`. The original model SHA-256 is checked before and after execution. The report is not evidence of model quality unless valid answers are captured.

## Windows validation

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_capture_chat_benchmark_v04283.py test_prepare_chat_benchmark_v04282.py test_persona_response_shadow_v0421.py
python capture_chat_benchmark_v04283.py --run --manifest results/chat_benchmark_manifest_v04282.json --checkpoint model/model-gpu-v1.6.2-online.pt --tokenizer model/tokenizer-v0.7-bpe.json --output results/chat_benchmark_capture_v04284.json --timeout-per-group 240
```

The previous v0.4.28.3 report remains immutable. Do not overwrite it.

Safety: This runner uses a temporary copy of project source/data but is NOT a complete file/network sandbox; review original data paths and the report before publication. Benchmark prompts are development data, not independent holdouts, and should never be used as training targets. No changes to `chat.py`, Truth Gate, or `/sleep` are made by this update.
