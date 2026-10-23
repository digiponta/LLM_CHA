# LLM_CHA v0.7.22 — Dual /sleep Learning

The interactive `/sleep` command now executes **two strictly separated
learning paths**:

1. PENDING Candidate Semantic Memory → frozen shared Base LLM +
   **Experimental Adapter training only**. Writes a new checkpoint under
   `results/experimental_sleep_v0722/`, leaves Candidate status PENDING.
2. Existing trusted Nagato/approved Semantic Sleep continues using the
   existing Trusted learning queue and checkpoint logic. No Candidate is
   inserted into this queue.

This design preserves the original `/sleep` semantics for the existing
Nagato memory while adding Experimental learning. It **does not train
PENDING Candidate information into Trusted weights**.

If there are no pending Experimental candidates, that part is skipped. If
the same snapshot has already been trained, the existing Experimental
checkpoint is reused. Adding a Candidate produces a new Experimental
checkpoint. Experimental failures cause the command to stop before the
Trusted step, rather than incorrectly report a successful dual sleep.

**Important:** this is not an atomic transaction across both independent
training steps. If Experimental succeeds and Trusted subsequently fails,
the Experimental checkpoint may still exist. Run `/sleep` again after
resolving the failure. The snapshot key includes the candidate records
and training hyperparameters but not the actual Base checkpoint bytes;
users who replace checkpoint bytes in place should use a new experiment
output directory or delete only the obsolete Experimental snapshots.

At present, v0.7.21's constrained runtime does not automatically load
the newly created v0.7.22 checkpoint. This new `/sleep` makes Experimental
knowledge trainable and persistent; selecting the new checkpoint for
generation is a subsequent explicit integration task. The `evidence`
Memory-First mode continues to read Candidate Semantic Memory directly.

## PowerShell
```powershell
git fetch origin
git switch --track origin/v0.7.22
python -m unittest -v test_experimental_sleep_v0722.py test_dual_runtime_bridge_v0721.py
python chat.py
```
Type `/sleep` once or twice. Inspect
`results/experimental_sleep_v0722/` for the Experimental-only adapter.
Training uses rank 16, 30 epochs, learning rate 1e-3 by default and requires
the existing local Base checkpoint and tokenizer. Actual GPU time depends
on the number of PENDING candidates.

No automatic promotion, factual verification, or Approved Memory modification
is performed by the Experimental path.
