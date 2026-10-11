# LLM_CHA v0.2.33.78 — Extended End-to-End Conversation Benchmark

The earlier v0.2.33.77.5 Windows GPU run completed with 4/4 matching transcript patterns, process return code 0 and no stderr. This branch adds a **separate, opt-in** extended benchmark instead of changing that passing script.

### What is measured

Five acceptance scenarios (four original cases plus a reference variation) must each match **both** route and answer patterns. Three extra cases are **exploratory**: mixed greeting variation, repeated greeting and thanks. They are reported but do not affect the acceptance PASS/FAIL result. A blank expectation is marked **not evaluated**, not a pass. The report contains per-case expected-pattern mismatches, a short transcript preview, separate routing and final-answer checks, stdout/stderr tails and subprocess diagnostics.

This is **not** a reliable general semantic-quality, robustness, unknown-rejection or persona accuracy benchmark. It is a small fixed-scenario runtime regression. The exploratory variants may expose regressions but cannot be called verified without establishing gold expectations.

### Run on Windows

```powershell
git fetch origin
git switch v0.2.33.78
git pull origin v0.2.33.78
python -m py_compile extended_chat_runtime_v023378.py
python -m unittest -v test_extended_chat_runtime_v023378.py
python extended_chat_runtime_v023378.py
python extended_chat_runtime_v023378.py --run --timeout 240
```

Report: `results/extended_chat_runtime_v023378.json`. Please share `acceptance_matched/acceptance_total`, `diagnostic` and per-case `route_pass`/`answer_pass`. This copied-checkout test is not an OS security boundary. Model weights and truth evidence are not intentionally changed.
