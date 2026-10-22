# LLM_CHA v0.7.7 — Adapter Learning Capacity Sweep

This branch runs a **27-condition sweep** of the Experimental Adapter:
`rank ∈ {8,16,32}`, `epochs ∈ {10,30,100}`,
`learning_rate ∈ {1e-4,3e-4,1e-3}`.

Every condition is trained against the same frozen Base checkpoint and
PENDING Candidate Memory, with a unique output folder and checkpoint.
No approved knowledge is promoted, no Trusted Adapter is trained, and no
production model or `chat.py` is changed.

For each condition, scripts run:
1. `train_experimental_adapter_v073.run` — isolated training
2. `evaluate_dual_adapter_v074.run` — teacher-forced candidate NLL
3. `diagnose_generation_v076.run` — greedy output, first-token rank,
   exact match, EOS diagnostics, plus approved probes if any.

## Run on Windows

```powershell
git fetch origin
git switch --track origin/v0.7.7
python -m unittest -v test_adapter_sweep_v077.py test_generation_diagnostic_v076.py
```

Small two-condition smoke test:

```powershell
python sweep_adapter_capacity_v077.py --limit 2 --output-dir results/adapter_sweep_v077_smoke
```

Full 27-condition sweep:

```powershell
python sweep_adapter_capacity_v077.py --output-dir results/adapter_sweep_v077_full
```

Results:
- `results/adapter_sweep_v077_full/summary_v077.json`
- `results/adapter_sweep_v077_full/summary_v077.csv`
- Individual condition folders containing adapter checkpoint, quality JSON,
  and generation diagnostic JSON.

The output directory must be fresh for each run. Distinct names ensure
experimental model checkpoints never overwrite each other.

## Interpretation

- `nll_delta < 0`: improved teacher-forced candidate NLL.
- `first_token_rank_experimental` smaller than Base: reference's first
  token has increased rank, but this alone does not establish correct generation.
- `candidate_exact_experimental`: greedy *training-set* exact match.
- `approved_count == 0`: cannot establish preservation of trusted answers;
  `quality_pass` is null, not a pass.
- Each tested candidate may have been seen during training; results are
  **not an independent holdout** or a factual correctness evaluation.
- Sweeps are diagnostic; **do not select by training performance alone**.
  Additional independent holdout and stability suites are required before
  any production routing or promotion.

**Caution:** the 100-epoch and 1e-3 settings may produce severe overfitting.
They are experiments, not recommended deployment settings.
