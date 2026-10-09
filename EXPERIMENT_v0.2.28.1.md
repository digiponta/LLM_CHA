# LLM_CHA v0.2.28.1 — Generation Trajectory Diagnosis

Experimental diagnostic only, no extra training.

## Motivation
v0.2.28 yielded lower validation loss (5.116545 vs baseline 5.250648) and
lower teacher-forced later NLL on sampled topics, while six raw greedy
single-turn outputs remained largely unchanged. Distinguish wrong initiation
from inability to continue a correct topical prefix.

## Experiment
Three frozen models: v0.2.27 baseline, v0.2.27.1 context selective,
v0.2.28 context persistence.

For each synthetic topic and both single and training-format prompts:
- free: full greedy model output
- first_k: prepend first eight **reference BPE tokens**, then greedy continuation
- first_half: prepend first floor(N/2) reference BPE tokens, then greedy continuation

Evaluate only the **generated continuation** for conditional continuation
quality. The complete_answer field includes intervention-forced material and
must never be presented as free model success.

## Commands
```powershell
git fetch origin
git switch v0.2.28.1
python -m unittest -v test_generation_trajectory_v02281.py
python diagnose_generation_trajectory_v02281.py
```

Output: results/generation_trajectory_v02281.jsonl

## Interpretation
- If free fails while first_k continuation grounds the topic, prioritize
  improved initiation/decoding.
- If first_k fails but first_half succeeds, focus on sustaining context
  through middle generation.
- If all fail despite teacher-forced NLL gains, address exposure bias,
  weak free-running generalization, model/data limits and decoding separately.
- If outputs are mixed, expand held-out cases and control for seed/formats.

**Cautions:** fixed prefixes are counterfactual interventions, not model
predictions; training-format reference answers can come from training data,
so these results are not an independent held-out benchmark. Prompt format and
EOS behavior must be considered. Do not modify trained checkpoints.
