# v0.7.44.4 — Bounded Response Controller (prototype)

Standalone opt-in controller. **Not connected to chat.py.**

```powershell
git pull
python -m unittest -v test_response_quality_gate_v07443.py test_response_controller_v07444.py
```

`controlled_response(generate, ...)` receives a callable taking an attempt number.
It retries on RETRY at most `retry_limit` times; HOLD blocks generated
unverified evidence and REVIEW requires an external reviewer. The REVIEW
path currently produces the safe fallback, not autonomous second-stage
review. ACCEPT returns the response unchanged. Fallback is a fixed,
nonfactual statement and must not overwrite Approved or Candidate state.

Limitations: no integration into the existing chat runtime, no GPU
generation acceptance test, no Japanese fluency metric and no end-to-end
persona recovery. The output gate cannot establish factual correctness.
