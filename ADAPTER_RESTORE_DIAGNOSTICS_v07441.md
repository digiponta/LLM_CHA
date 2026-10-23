# LLM_CHA v0.7.44.1 — Experimental Adapter Restore Diagnostics

Branch: `v0.7.44` (based on `v0.7.43`).

This initial diagnostic is **read-only**, and does not change `chat.py`, the
production Trusted checkpoint, Approved Memory, Candidate Store, or Wikipedia
fallback. It validates that an experimental checkpoint is present, readable,
and contains a recognizable PyTorch tensor state dictionary. Optional state
files are checked for existence and basic JSON/JSONL validity.

## Usage (PowerShell)

```powershell
git fetch origin
git switch --track origin/v0.7.44
python -m unittest -v test_adapter_restore_v07441.py
python diagnose_adapter_restore_v07441.py --checkpoint results/approved_paraphrase_v0743/experimental-trusted.pt --state results/approved_paraphrase_v0743/learning_state.json --output results/restore_diagnostic_v07441.json
```

Interpretation: `PREFLIGHT_OK` is **not** successful runtime restore.
`PREFLIGHT_ONLY` only checks files. The production `LanguageModel.load_checkpoint`
path, adapter-specific schema, model architecture, Semantic Memory ID/fingerprint
binding, and Candidate Store linkage must be checked in v0.7.44.2. A
`CHECKPOINT_CORRUPT` from the safe tensor-only loader may instead be an
older custom-object checkpoint; the diagnostic deliberately does not call
`torch.load(..., weights_only=False)`. Inspect such files only in a trusted
environment. The CLI exits nonzero for failures.

Never interpret APPROVED as scientifically TRUE; UNVERIFIED statements remain
UNVERIFIED even if the checkpoint passes preflight.
