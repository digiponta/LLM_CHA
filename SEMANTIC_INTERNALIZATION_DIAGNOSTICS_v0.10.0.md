# v0.10.0 Semantic Memory internalization diagnosis

Startup counters are produced by `semantic_sleep_status` in `semantic_sleep_learning_v10131.py`. It treats a memory fingerprint as internalized only when it appears in BOTH `learning_state` and the loaded checkpoint's `metadata.trained_fingerprints`. Thus `internalized=0` does not, by itself, establish that trained weights were lost.

The new read-only startup line `[semantic_internalization_audit=...]` reports memory, learning-state, and checkpoint fingerprint counts and overlaps, plus a cause classification. It does not modify the checkpoint, change learning metadata, or run `/sleep`.

Windows check:

```powershell
python -m unittest -v test_audit_semantic_internalization_v0100.py
python chat.py
```

Inspect `status`, `learning_state_count`, `checkpoint_count`, `memory_in_learning_state`, `memory_in_checkpoint`, and `learning_checkpoint_shared`. `checkpoint_weights_verified=false` remains true until a separate empirical evaluation validates the weights.

No automated repairs are performed; keep checkpoint and training-state evidence intact before considering reconciliation.
