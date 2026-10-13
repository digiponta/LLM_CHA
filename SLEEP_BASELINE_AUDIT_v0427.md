# LLM_CHA v0.4.27 — Sleep Baseline Audit

This is an **evaluation-only first stage** toward safe /sleep consolidation. Existing `/sleep` currently prepares semantic and conditional learning pairs, calls `run_online_training` and reloads the resulting checkpoint. This code does **not** change that route and does not trigger training.

`sleep_baseline_audit_v0427.py` compares two real runtime-capture JSONL snapshots with exactly matching question sets and reports answer changes and changes in agreement and semantic agreement. It does not automatically infer response correctness, verify whether the checkpoint actually changed, establish causality, or claim a sealed holdout.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_sleep_baseline_audit_v0427.py test_persona_quality_dimensions_v0426.py test_persona_quality_workflow_v0425.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

## Experimental protocol

1. Choose a **fixed** set of new test questions before any sleep experiment. Include direct knowledge, paraphrase, daily conversation and persona-retention cases. Keep the question list and decoding configuration identical for both runs.
2. With `/capture on`, run the questions using the **pre-sleep** checkpoint, and copy the resulting capture records into `results/sleep_before_v0427.jsonl`. Do not mix with historical development captures. Store the checkpoint identity and SHA256 separately and record model config and runtime flags.
3. Back up model checkpoint, learning state, queues and evaluation data *before* any optional /sleep. **Do not run /sleep merely to run this audit**. The current /sleep path has not been shown to have candidate promotion/rollback safety.
4. If a controlled, separately approved sleep experiment is performed, run the exact same questions with the after checkpoint and copy actual captures into `results/sleep_after_v0427.jsonl`. Ensure each file has one record per unique question.
5. Run the comparator:

```powershell
python sleep_baseline_audit_v0427.py --before results/sleep_before_v0427.jsonl --after results/sleep_after_v0427.jsonl --report results/sleep_baseline_report_v0427.json
```

Review changed and unchanged answers manually. Better automatic safeguards (human-reviewed paired quality labels, checkpoint binding, candidate checkpoint testing and rollback) remain work for later versions. **No improvement should be claimed merely because the answer changed or the semantic agreement rose.**

Never upload sensitive chat records to public GitHub. This version is read-only and touches neither Truth Gate nor Semantic Memory nor /sleep internals.
