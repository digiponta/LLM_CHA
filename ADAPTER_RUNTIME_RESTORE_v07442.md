# v0.7.44.2 — Runtime Restore Verification

Run in PowerShell:

```powershell
git pull
python -m unittest -v test_adapter_restore_v07441.py test_adapter_restore_v07442.py
python verify_adapter_restore_v07442.py --checkpoint results/approved_paraphrase_v0743/experimental-trusted.pt --state results/approved_paraphrase_v0743/learning_state.json
```

The verification calls the actual `LanguageModel.load_checkpoint()` with the CPU device, then compares `metadata.trained_fingerprints` against `learning_state.json.trained_fingerprints`. It does not sample any text, promote any evidence, alter the production checkpoint, or certify the Experimental Adapter's higher-level startup path.

`RESTORE_OK` means the model loaded and the supplied learning-state fingerprints matched. `FINGERPRINT_MISMATCH` highlights binding inconsistency; non-matching files are NOT automatically repaired. Be aware that the existing model loader invokes `torch.load` on the checkpoint; only run this verifier with your own trusted checkpoint.

Next: adapter startup-path roundtrip, Approved/Candidate IDs and fingerprint audit, persona-gap response-quality gating.
