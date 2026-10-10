# LLM_CHA v0.2.33.23 — Copy Mechanism Diagnostic

## Why

v0.2.33.22 found:
- **Long** 0/40 in every arm, including training length 2–18.
- **Expanded ID pool** improves from 4/40 (baseline) to 19/40 (combined).
- **Novel Only IDs** still 0/40 in all arms.

This read-only study differentiates source sensitivity, token selection and EOS behavior. It is *not* a demonstration that a particular attention head causes copying.

## Mechanism probes

For each fresh token-ID source of length 2–8 or 12–18:
1. Pick one random source position `j`.
2. Compute next-token distribution for the **gold output prefix** `BOS MARKER source MARKER source[:j]`.
3. Replace only source position `j` with another known ID; then repeat with a task-unseen ID (88–103). Keep all previous generated tokens fixed. Compare both old and new ID probabilities, rank, and Top-1 selection.
4. Independently compute multi-head attention weights at that prediction step from each block's Q/K projections; report weight and rank for the matching source position and most-attended input position.
5. At each teacher-forced output step record EOS probability, plus EOS probability at correct completion.

Models (frozen):
- `model/model-llm-cha-algorithmic-copy-v023320.pt`
- `model/token_copy_factorial_v023322/combined.pt`

Neither the original checkpoints nor DSS/Semantic Memory/Bridge is changed. Attention weights are not proof of causal copying: source interventions provide a more direct *behavioral* dependence test, but cannot localize it to a specific attention head.

## Run

```powershell
git fetch origin
git switch v0.2.33.23
git pull origin v0.2.33.23
python -m unittest -v test_copy_mechanism_v023323.py
python diagnose_copy_mechanism_v023323.py
```

Output: `results/copy_mechanism_diagnostic_v023323.json`, with per-case source mutation, probability shifts, attention descriptions, and EOS probabilities. Reruns must use a new `--out` path.

## Interpretation

- Positive probability gain on new token ID but low rank: source token affects predictions, but output decoding distribution or competing token biases may be limiting.
- No probability response to replacing source: learned source copying is weak for these probes.
- Early-EOS probability spikes with length: termination calibration is a candidate.
- Attention to matching source may correlate with copying, but *does not* establish a causal route. Controlled attention ablation would be a distinct experiment.

Use these results to decide between data/training adjustments, loss rebalancing, explicit copy mechanisms, or further causal tests. Do not promote an experimental checkpoint based on these diagnostics.
