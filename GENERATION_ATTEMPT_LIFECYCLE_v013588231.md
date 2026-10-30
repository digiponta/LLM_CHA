# LLM_CHA v0.13.58.82.31 — Generation Attempt Lifecycle Diagnostics

A prior GUI log showed an Evidence fallback but `/genstats` reported `cases: 0`. The earlier counter only measured completed branches, giving no visibility into retrieval/LLM attempts in progress or failed before the normal callback.

This release introduces a distinct `AttemptTracker` on the GUI, starting an Attempt ID when the user requests elaboration and tracking states STARTED, WAITING_LLM, COMPLETED, FAILED. `/genstats` and `/gencompare` include `lifecycle` with attempts_started, in_flight, completed, failed and state counts. Existing gate counters remain separate, so mismatches can be diagnosed.

Caveats: a pending LLM response never delivered by the subprocess remains in-flight; timeout/automated expiry is not yet implemented. GUI restarts reset these session-only counts. This release instruments the lifecycle and does not guarantee improved generation accuracy.

## Windows validation
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.31-attempt-lifecycle
python -m unittest -v test_generation_attempt_tracker_v013588231.py test_generation_diagnostics_v013588230.py test_single_turn_conditioned_v013588229.py
python chat_gui.py
```

Try `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく`, then `/genstats`. Confirm `attempts_started >= 1`, and inspect the diagnostic log for `[Generation Attempt STARTED]` and `[Evidence Gate]`.
