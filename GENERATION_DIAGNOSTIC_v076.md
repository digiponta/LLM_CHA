# LLM_CHA v0.7.6 — Generation Failure Diagnostics

The v0.7.5 offline evaluation showed zero exact free-generation answers for
Base / Trusted / Experimental, despite small NLL improvements after training.
This branch investigates *why*, without updating model weights.

## Diagnostics

For each PENDING Candidate and optional Approved probe, records:
- Raw generated text from all three inference routes.
- Stop reason (EOS or token limit) and number of generated tokens.
- First reference-answer token rank and probability.
- Exact match, empty output and prefix-match checks.
- Approval probe count; `quality_pass` remains `null` pending evaluation.

## Windows commands

```powershell
git fetch origin
git switch --track origin/v0.7.6
python -m unittest -v test_generation_diagnostic_v076.py test_dual_inference_v075.py
python diagnose_generation_v076.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --adapter results/adapter_sandbox_v073/experimental-adapter.pt `
  --report results/generation_diagnostic_v076.json
```

Review `results/generation_diagnostic_v076.json` for actual text and first-token
rank. A candidate used in training is **not** a holdout. Approved probe coverage
is still empty unless Approved JSONL contains records; do not invent approvals
for a meaningless test phrase. All generation is greedy and no extra learning
takes place.

## Next planned work

After diagnosing outputs, run controlled rank / epoch / learning-rate sweeps
with separate checkpoints and independent holdout questions. Keep candidate
experiments distinct from approved / production inference.
