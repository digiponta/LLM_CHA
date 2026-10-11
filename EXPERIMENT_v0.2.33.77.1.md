# LLM_CHA v0.2.33.77.1 — Runtime Benchmark Startup Diagnostics

## Previous observation

Windows unit tests **12/12 PASS**, but `python chat_runtime_benchmark_v023377.py --run --timeout 240` exited after 2.8 seconds with `process_returncode=1`, `passed=0/4`. That does **not** demonstrate that the four conversation policies failed; it suggests an early subprocess error. The actual `stderr_tail` was not yet provided, so the cause is **unknown**.

This patch to `chat_runtime_benchmark_v023377.py` records a `diagnostic` object with distinct phases: `STARTUP_ERROR`, `STARTUP_OR_RUNTIME_ERROR`, `TIMEOUT`, or `EVALUATION`. On subprocess failure, all cases are marked `not_evaluated_runtime_failure`, never misrepresented as policy failures. Errors and exception summary are printed to the Windows console, while full stderr tail remains in the JSON report. Existing temporary-copy isolation and opt-in `--run` remain unchanged.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.77.1
git pull origin v0.2.33.77.1
python -m py_compile chat_runtime_benchmark_v023377.py
python -m unittest -v test_startup_diagnostics_v0233771.py test_chat_runtime_benchmark_v023377.py
python chat_runtime_benchmark_v023377.py --run --timeout 240
```

Please share the console `diagnostic:` and `stderr_tail:` outputs. The test harness may still need a fix for the actual startup exception; this version first makes that root cause visible. It does not modify `chat.py`, Semantic Memory, Truth States, or model weights.
