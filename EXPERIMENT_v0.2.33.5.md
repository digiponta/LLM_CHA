# LLM_CHA v0.2.33.5 — Language Foundation Recovery

## Research goal

Before retraining Semantic-to-Generation Bridge, test whether the **base LLM** can learn minimal Japanese explanation, procedure, context, conditional response and sentence continuation behavior through response-only SFT.

**This is a deliberately small proof-of-mechanism pilot, not sufficient for robust Japanese language competence.** It contains only 14 authored training samples, 4 different validation prompts, and 8 held-out free-generation probes. Do not infer language understanding or readiness for semantic internalization solely from a loss reduction.

DSS, Semantic Memory, existing Bridge implementations, all former checkpoints and normal chat routing are **unchanged**.

## Experiment

- Train starting from `model/model-llm-cha-response-quality-v0221.pt`.
- Response-token-masked SFT of the base LLM using differential LR for Transformer and LM head.
- Replay of prior basic responses to reduce forgetting.
- Select best checkpoint according to validation NLL (not the training set).
- Evaluate **Base vs Foundation** using 8 unseen prompt strings, greedy generation with equal token budget.
- Review correctness and fluency manually. The free-generation probes are authored with the code and are exploratory rather than independently sealed.
- No automatic promotion, no memory modifications or live routing switch.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.5
git pull origin v0.2.33.5

python -m unittest -v test_language_foundation_recovery_v02335.py
python language_foundation_recovery_v02335.py train --epochs 12
python language_foundation_recovery_v02335.py evaluate
```

Outputs:
- `model/model-llm-cha-language-foundation-v02335.pt`
- `results/language_foundation_train_v02335.json`
- `results/language_foundation_eval_v02335.json`

Separate before/after comparison against v0.2.33.4 foundational probes can be run with:

```powershell
python evaluate_language_generation_baseline_v02334.py `
  --compare model/model-llm-cha-language-foundation-v02335.pt `
  --out results/language_generation_compare_foundation_v02335.json
```

## Next checkpoint

If free-generation **meaningfully** improves, train a *new* Semantic Bridge against the foundation checkpoint using explicit input/output path overrides; do **not** reuse a bridge trained against the original base without evaluating compatibility. If no improvement, revise the underlying language corpus/pretraining and study tokenization or generation mismatch before adding semantic components.

Do not overwrite an existing output when re-running.
