# v0.13.58.82.32 — Generation Failure Root-Cause Diagnostics

A user test showed attempts_started=1, completed=0, failed=1, cases=0. Previously the lifecycle tracked FAILED but did not expose its underlying reason.

This update adds `failure_reasons` and the five latest attempt records to `/genstats` and `/gencompare` lifecycle output. The records include Attempt ID, topic, gate, failure reason, Python exception type (if any), prompt length and whether the subprocess was alive at failure. The diagnostics tab also prints `[Generation Send Failure] ExceptionName: message`. Private candidate content is not included in the report.

For a successful inference request, Attempt must transition to WAITING_LLM, then COMPLETED. A stopped subprocess is marked NO_MODEL; a caught send or input-validation exception is marked SEND_FAILED with exception type. This narrows down the cause; it does **not** yet guarantee that inference generation or acceptance will improve.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.32-generation-failure-diagnostics
python -m unittest -v test_generation_failure_diagnostics_v013588232.py test_generation_attempt_tracker_v013588231.py
python chat_gui.py
```

Try `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく`, `/genstats`. Examine `lifecycle.failure_reasons`, `recent_attempts` and the diagnostics tab for a precise exception. If SEND_FAILED and exception_type is ValueError, the exception message distinguishes multiline validation, closed stdin and other ValueErrors. If NO_MODEL, inspect whether chat.py exited.
