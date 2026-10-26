# Semantic checkpoint reconciliation (v0.10.0)

The observed current Semantic Memory contains 56 unique fingerprints, both online and candidate checkpoints contain all 56 plus five other fingerprints, and chat_learning_state.json has an empty trained_fingerprints list. The default model selection in chat.py therefore selects the baseline rather than the existing online checkpoint.

The reconciliation script is read-only by default. An explicit --apply with --checkpoint checks complete memory coverage, requires an existing empty learning-state list, saves a non-overwriting backup named chat_learning_state.json.pre-reconcile.bak, and updates the state atomically. The checkpoint model is not changed. After applying against model-gpu-v1.6.2-online.pt, the normal chat.py startup will select the online checkpoint. This changes runtime model selection and must be tested with quality probes.

Commands:

```powershell
python -m unittest -v test_reconcile_semantic_checkpoint_v0100.py
python reconcile_semantic_checkpoint_v0100.py --checkpoint model/model-gpu-v1.6.2-online.pt
# Inspect READY_FOR_EXPLICIT_RECONCILIATION before electing to apply:
python reconcile_semantic_checkpoint_v0100.py --checkpoint model/model-gpu-v1.6.2-online.pt --apply
python chat.py
```

The metadata reconciliation does not prove accuracy of answers encoded in model weights. Do not substitute the candidate checkpoint for the online checkpoint without separately selecting/validating it. No Windows validation has been performed yet.
