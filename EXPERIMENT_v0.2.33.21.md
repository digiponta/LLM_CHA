# v0.2.33.21 — Algorithmic Copy Error Analysis

## Previous result

v0.2.33.20: single-seed, algorithmic token-ID copy task; **train 357/400, validation 28/80, test 36/80, long 0/40, held-out IDs 0/40, mixed IDs 3/40**. Core training is viable, but the location and character of copying errors are unknown.

## Purpose

Read-only diagnostic of `model/model-llm-cha-algorithmic-copy-v023320.pt`. No training, no checkpoint writes, no changes to DSS, Semantic Memory or Bridge.

- **Length sweep:** fresh sequences, lengths 2–18, 12 per length by default, drawn from the *known* ID pool.
- **Token diagnostics:** teacher-forced top-1 accuracy, per-token ranks, probability/rank of first copied token and EOS.
- **Free-generation diagnostics:** exact ID copy including EOS, contiguous correct prefix, first wrong position.
- **Failure categories:** early EOS, late EOS, EOS missing/wrong, content mismatch.
- **Vocabulary:** reproduce the historical held-out-ID, mixed-ID and held-out in-pool tests from v0.2.33.20 with seed 42, clearly marked as non-independent.

A new length-sweep generated from known IDs is diagnostic rather than a fresh independent final benchmark. It does not use results to adjust weights or select checkpoints.

## Run on Windows

```powershell
git fetch origin
git switch v0.2.33.21
git pull origin v0.2.33.21
python -m unittest -v test_algorithmic_copy_errors_v023321.py
python diagnose_algorithmic_copy_errors_v023321.py
```

Result: `results/algorithmic_copy_errors_v023321.json`.

The report includes per-example token-ID sequences; it can become large. The script refuses to overwrite existing reports; use a new `--out` value to rerun.

## Interpretation

- Teacher-forced accuracy high but free generation low: exposure bias / autoregressive propagation likely contributes.
- Many early-EOS cases: study EOS supervision and diverse training lengths.
- Token errors increase toward later positions: study positional extrapolation and sequence curricula.
- Held-out IDs fail even in short sequences: investigate ID-specific representation and input–output copying mechanisms.
- Length 2–8 successes with lengths 9+ collapse: confirms training-range limitation. Do not infer that longer-context numerical masking is faulty without further verification.

This does not establish causal attribution to any attention head. Such conclusions require controlled interventions.
