# LLM_CHA v0.2.34.5 — Context Recovery Hardening

**Experimental**, branch `v0.2.34-longterm-context`. No stable tag or production data changed.

Improvements:
- Save writes JSON into a same-directory temporary file, flushes + `fsync`s, then atomically replaces the checkpoint using `os.replace`. If the replacement fails, the previous checkpoint is retained and the temporary file is deleted.
- Load checks checkpoint byte size (128 KiB maximum) before reading and still validates schema/truth before changing live context.
- New regression tests cover multi-topic cursor restoration, simulated replacement failure, oversized corrupt input, and changed subject Truth State.
- Note: atomic replacement is not full durability across hardware/power failure, nor a multi-process transaction. Corpus can still change between validation and presentation, and the adapter uses current policy from each read.

## Windows validation

```powershell
git switch v0.2.34-longterm-context
git pull --ff-only origin v0.2.34-longterm-context
python -m unittest -v test_longterm_context_v02340.py test_context_restore_validation_v023341.py test_corpus_restore_adapter_v023342.py test_context_recovery_v023343.py test_context_recovery_integration_v023343.py test_context_recovery_gpu_accept_v023344.py test_context_recovery_hardening_v023345.py
python context_recovery_gpu_accept_v023344.py --timeout 240
python verify_conditional_runtime_stable_v10165.py
```

Expected new cumulative unit tests: **47/47** (prior 43 plus four); GPU acceptance remains **14/14**. These results are **not yet executed** on the user's local GPU. Full v0.2.33.82 94-case regressions should also be rerun before a candidate release.
