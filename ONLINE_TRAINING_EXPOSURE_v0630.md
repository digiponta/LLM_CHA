# LLM_CHA v0.6.30 — Online Training Exposure Accounting

## Purpose
The historical v0.6.29 audit found 60 trusted fingerprints in both the
learning-state file and the checkpoint, but no historical proof of which
examples reached an optimizer step. Their status remains **unverified**.

## New runs
- Hold pending trusted pairs in training, never validation-only (v0.6.28 fix).
- Use an index-aware training DataLoader.
- Count fingerprint exposure only after `optimizer.step()` completes.
- Refuse to mark pending fingerprints trained when any pending pair has zero
  recorded exposure.
- Save `training_exposure_counts_v0630` inside the output checkpoint.
- Do not rewrite past exposure counts or automatically re-train old records.

## Check

```powershell
git fetch origin
git switch --track origin/v0.6.30
python -m unittest -v test_training_exposure_v0630.py test_online_validation_coverage_v0628.py test_audit_online_learning_v0629.py
```

This checks coverage and guards, but does not substitute for GPU integration
testing of checkpoint save/load, parameter updates, and quality regression.

## Caution
Exposure counts indicate an optimizer step executed for a training batch
containing the sample. They do **not** prove that the learned answer was
retained, or that its gradient was individually nonzero. Use additional
holdout and forgetting tests before trusting the resulting model.
