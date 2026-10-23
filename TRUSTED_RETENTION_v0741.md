# LLM_CHA v0.7.41 — Trusted Approved Knowledge Retention Audit

Adds read-only `verify_trusted_retention_v0741.py`. It compares
Approved Knowledge target-token negative log-likelihood (NLL) and
stability replay NLL on explicit Trusted checkpoints, and audits whether
the Approved pair fingerprints occur in both learning state and the
loaded checkpoint's metadata.

**Important:** the v0.7.40 /sleep run overwrote
`model/model-gpu-v1.6.2-online.pt`. Therefore the real pre-/post-
comparison is only possible when a copy of the original checkpoint
exists. If it does not, run without `--before`: this produces an
AFTER-only diagnostic and does not invent a baseline.

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.7.41
python -m unittest -v test_trusted_retention_v0741.py test_approved_semantic_sleep_v0740.py
python verify_trusted_retention_v0741.py
```

If an actual pre-sleep file exists, use:

```powershell
python verify_trusted_retention_v0741.py --before model/YOUR_PRE_SLEEP_CHECKPOINT.pt --after model/model-gpu-v1.6.2-online.pt
```

Inspect `results/trusted_retention_v0741.json`, especially
`checkpoint_bound_count`, `approved_nll_gain` (lower after is
better) and `stability_nll_change` (higher after may indicate
forgetting). These are **teacher-forced measurements only**:
free-generation accuracy and actual generalization remain unverified.
No retraining and no changes to weights or knowledge stores are made.
