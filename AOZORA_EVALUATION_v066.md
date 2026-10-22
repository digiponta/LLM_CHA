# LLM_CHA v0.6.6 — Baseline vs Aozora checkpoint comparison

Compares raw checkpoints using the same BPE tokenizer and held-out work,
plus deterministic greedy outputs for five fixed prompts. **This is not**
a persona or dialogue quality PASS: manual review and the actual
`chat.py` runtime regression are required.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.6.6
# If local v0.6.6 exists: git switch v0.6.6
python -m unittest -v test_evaluate_aozora_models_v066.py
python evaluate_aozora_models_v066.py
Get-Content results/aozora_comparison_v066.json -Encoding utf8
```

This loads `model/model-llm-try-nagato-chat-v94.pt` and
`model/model-llm-cha-aozora-v065.pt`, then saves
`results/aozora_comparison_v066.json`. Existing result files cannot
be overwritten. Use `--output` for a new experiment.

Metrics:
- mean next-token NLL on held-out work 1567 (走れメロス), with fragment
  context reset and a common token budget
- mean NLL on a capped sample of training work 789 (吾輩は猫である)
- raw text samples from both models using identical greedy decoding

The original v0.6.5 log evaluated a different windowing strategy,
so its numerical NLL values should not be compared directly with v0.6.6.
Only compare values *within* the v0.6.6 report.

Do not promote the Aozora checkpoint based on NLL alone. Verify persona
answers, general conversation, Truth Gate, unknown rejection, semantic
memory, and `/sleep` via the actual runtime. No model weights,
Semantic Memory, or training data are modified by this comparison.
