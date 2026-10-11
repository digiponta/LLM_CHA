# LLM_CHA v0.2.33.77 — Automated Chat Runtime Evaluation (experimental)

This branch adds `chat_runtime_benchmark_v023377.py`, an **opt-in real subprocess evaluation** that copies the project checkout (including data/model files) to a temporary directory, starts `chat.py --session-reference-memory` there, sends four prompts through standard input, captures console output, and evaluates exact expected markers.

The user must explicitly pass `--run`. Without it no subprocess is started. The temporary copy is deleted when finished; output JSON is written to the original `results/` location. This protects the original checkout against **ordinary relative-path writes**, but is **not a security sandbox**: Python imports or absolute paths may produce other side effects. Do not run against untrusted code, and back up valuable data before experimenting.

## Covered prompts

1. `こんにちは`: final natural greeting / quality fallback marker
2. `こんにちは、宇宙について教えて`: mixed intent / unverified truth block
3. `宇宙とは`: unverified truth block / no corpus answer
4. `昨日の続き`: explicit reference clarification

Tests assume the default truth state for `宇宙` is UNVERIFIED. Local changes to Truth State may legitimately change outcomes; do not manipulate Truth State just to pass a test. Piped Python input is **not echoed**, so the scorer assigns prompts to consecutive `You> ` markers, not by matching user texts in stdout. GPU behavior, subprocess errors and timeout are recorded. The benchmark checks trace markers, **not semantic response quality**, long-turn reference consistency or all truth paths.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.77
git pull origin v0.2.33.77
python -m py_compile chat_runtime_benchmark_v023377.py
python -m unittest -v test_chat_runtime_benchmark_v023377.py test_integration_policy_benchmark_v023376.py

# Dry-run first: does not start a subprocess
python chat_runtime_benchmark_v023377.py

# Explicit GPU runtime execution in temporary checkout
python chat_runtime_benchmark_v023377.py --run --timeout 240
```

Result: `results/chat_runtime_v023377.json`. A nonzero exit code indicates an unmet expectation, runtime failure, or timeout. The report contains captured output excerpts (which may reveal user/model text); review before sharing publicly. A full diagnostic should inspect both `process_returncode` and per-case results. No model weights, training data, or real Semantic Memory are intentionally modified.

**Limitations**: copying an entire model can consume disk space and time. The suite only uses four deterministic expected checkpoints; to generalize research claims requires a separate dataset, evidence-grounded human gold and actual model generation quality measurements.
