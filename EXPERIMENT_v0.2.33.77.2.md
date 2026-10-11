# LLM_CHA v0.2.33.77.2 — Isolated Runtime Preflight

The v0.2.33.77 automated runtime previously returned **0/4** with process exit 1 after 2.8 seconds. The cause remains undetermined without the actual stderr output.

This version adds **read-only preflight checks** for the default model, tokenizer, corpus and PyTorch before starting the subprocess. The same checks run on the temporary checkout before GPU startup. If the temporary copy cannot see required files, the evaluator reports `PREFLIGHT_ERROR`, lists missing assets and marks the scenarios as **not evaluated**, rather than implying the LLM failed those prompts.

The preflight is intentionally conservative and checks default paths, not every custom model argument or import. A PASS does not mean that CUDA, model loading or chat initialization will succeed. Errors during initialization remain captured in `stderr_tail`.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.77.2
git pull origin v0.2.33.77.2
python -m py_compile chat_runtime_benchmark_v023377.py runtime_startup_preflight_v0233772.py
python -m unittest -v test_runtime_startup_preflight_v0233772.py test_startup_diagnostics_v0233771.py test_chat_runtime_benchmark_v023377.py
python chat_runtime_benchmark_v023377.py --run --timeout 240
```

The report remains `results/chat_runtime_v023377.json`. Please share the `diagnostic`, `preflight` and `stderr_tail` outputs. This commit **does not claim to fix an unknown error**; it makes absent runtime assets and dependency problems distinguishable from failing dialogue behavior.

Note: copying the project to a temporary folder is not an OS-level sandbox. No source files, model weights or truth records are intentionally modified.
