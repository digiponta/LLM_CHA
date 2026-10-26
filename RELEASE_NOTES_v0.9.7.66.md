# LLM_CHA v0.9.7.66 — Memory Status Diagnostics and GUI Version

This branch extends v0.9.7.65 without modifying neural weights, Semantic Memory records or /sleep.

Updates:
- GUI title uses checked-out Git branch (with v0.9.7.66 fallback).
- Read-only parser classifies `[Nagato Semantic Memory: ...]` startup counters.
- `inspect_memory_status_v09766.py` accepts `--line` or `--log`.
- Four unit tests cover the parser and version identifier.

The initial status `internalized=0, pending=56` is classified `PENDING_REINTERNALIZATION_CHECK`, not `CHECKPOINT_LOST`. This version cannot establish whether weights have changed; that requires a follow-up checkpoint/metadata inspection and, ideally, actual knowledge probes.

Windows verification:

```powershell
git fetch origin
git switch v0.9.7.66
git pull --ff-only
python -m unittest -v test_release_diagnostics_v09766.py test_causal_question_normalization_v09765.py
python inspect_memory_status_v09766.py --line "[Nagato Semantic Memory: corpus_records=72, subjects=56, unified_added=56, unified_preserved=0, internalized=0, pending=56]"
python chat_window_v061.py
```

Caution: this is a read-only diagnostic and GUI labeling release, not a memory recovery implementation. Windows tests have not yet been executed.
