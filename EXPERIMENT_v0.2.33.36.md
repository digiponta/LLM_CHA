# LLM_CHA v0.2.33.36 — DSS Unknown Resolution Adapter (Contract Experiment)

## What is implemented

This branch introduces `IntegrationResolver(dss, memory)` with **injectable** DSS and candidate-store adapters, explicit approval, rejection, cancellation, bounded clarification attempts, context-scoped approved values, turn-based TTL for pending dialogue, and memory invalidation. It explicitly does **not** call the live DSS/Semantic Memory because their callable Python API could not be reliably established from the available repository content. Defaults `MockDSS` and `LocalCandidateStore` are only in-process demonstrators.

The abstraction specifies expected DSS assessment fields (`kind,subject,slot,question,choices,value`) and candidate memory operations (`lookup,propose,approve,reject,invalidate`). For live integration, first inspect real DSS and Semantic Memory APIs, write minimal real adapters, then run a separate verification with a temporary store. Never silently auto-promote user responses or modify LLM weights.

A second, separate research workstream—Script-Conditioned Cursor/EOS Calibration—remains proposed but **is not part of this implementation**. Unknown token IDs in copying must not trigger user clarification.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.36
git pull origin v0.2.33.36
python -m py_compile dss_unknown_adapter_v023336.py
python -m unittest -v test_dss_unknown_adapter_v023336.py
python dss_unknown_adapter_v023336.py --demo
```

Report: `results/dss_unknown_adapter_v023336.json`. A repeat demo refuses to overwrite it.

## Acceptance criteria

1. Two-stage proposal/confirmation; no approved knowledge before consent.
2. No cross-session reference leakage.
3. Outdated/pending information can be rejected or invalidated.
4. Bounded retries and abstention.
5. No questions for unrelated token sequences.
6. No impact on stable DSS, Semantic Memory, Bridge or checkpoints.

## Limitations

Turn-based expiration only applies to **pending clarifications**. Approved memory remains context-scoped but not time-expired; a production adapter must add referent version IDs and provenance expiration to avoid replaying outdated 'yesterday' references. The mocked DSS is keyword-based and has no natural-language ambiguity detection or automatic candidate validation. This is a safe integration **boundary** and test harness, not a completed live integration.
