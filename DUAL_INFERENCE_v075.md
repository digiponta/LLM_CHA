# LLM_CHA v0.7.5 — Dual Inference / Free-Generation Evaluation

Offline experimental evaluation of three routes sharing a frozen Base LLM:
1. `base`: baseline model without an adapter.
2. `trusted`: untrained Trusted Adapter; never updated with pending knowledge.
3. `experimental`: candidate-trained adapter saved by v0.7.3.

Normal routing always selects `trusted`. An experimental route must be
explicitly selected with **both** `--mode experiment` and
`--allow-experimental`. The evaluation command computes all three
routes for comparison regardless of runtime selection; no external requests,
no `chat.py` integration, and **no automatic approval or promotion**.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.5
python -m unittest -v test_dual_inference_v075.py test_knowledge_promotion_v074.py
python dual_inference_v075.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --adapter results/adapter_sandbox_v073/experimental-adapter.pt `
  --report results/dual_inference_v075.json
```

Explicit experimental routing test:

```powershell
python dual_inference_v075.py --mode experiment --allow-experimental `
  --report results/dual_inference_experiment_v075.json
```

Results: candidate/approved reference answers, greedy generated answers for
all three routes, exact-match rates, selected runtime route and a conservative
quality decision. **If no Approved records are available, `quality_pass`
is `null` (not pass).** Candidate examples previously used for adapter
training are not independent holdout results.

Generation uses the same `人: ...\nAI: ` prefix used by the training
dataset. This is standalone experimental inference rather than the full
persona/Truth Gate routing of `chat.py`.

## Research boundaries

- Small samples cannot establish generalization or knowledge retention.
- Exact text matching underestimates semantically equivalent answers and
  cannot detect factual hallucinations.
- Model parameters and memory stores remain unchanged.
- Next: independent holdout sets and guarded runtime integration.
