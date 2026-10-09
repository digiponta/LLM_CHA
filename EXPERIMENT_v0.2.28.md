# LLM_CHA v0.2.28 — Context Persistence Learning

## Motivation from v0.2.27.2
Context-selective initiation raised teacher first-token probability in all three measured topics, but prior greedy raw responses were mostly unchanged. The matching training-format prompts did not uniformly improve the target probability. First-token probability alone is not a measure of full response grounding.

## v0.2.28 experiment
Keep baseline and v0.2.27.1 checkpoints untouched. Train from the same v0.2.21 base under the same exposure and optimizer settings using:
- standard loss over all response tokens
- initiation loss over context-sourced first 8 assistant tokens, lambda=0.5
- persistence loss over context-sourced response tokens strictly AFTER the first 8, late-weight=0.5

The late region is not further split into middle vs end yet. This experiment tests continuation weighting, not long-horizon multi-turn memory.

## Commands
```powershell
git fetch origin
git switch v0.2.28
python -m unittest -v test_context_persistence_v0228.py test_context_selective_v02271.py
python run_context_persistence_v0228.py --dry-run
python run_context_persistence_v0228.py --init-k 8 --init-weight 0.5 --late-weight 0.5
python evaluate_persistence_phases_v0228.py --model baseline=model/model-llm-cha-v0227-baseline.pt --model selective=model/model-llm-cha-context-selective-v02271.pt --model persistence=model/model-llm-cha-context-persistence-v0228.pt
python diagnose_raw_runtime_v02271.py --model model/model-llm-cha-context-persistence-v0228.pt --out results/raw-persistence-v0228.jsonl
```

## Limitations
- Teacher-forced phase NLL uses synthetic reference responses. It measures likelihood, NOT raw free-generation quality.
- Some topic examples used for this scripted diagnostic are from training. No independent holdout generalization claims may be made from their scores.
- Required next checks: held-out topics and multi-turn prompt comparisons; raw-greedy response grounding; general conversation/persona retention; seed/variance replication.
- No results for v0.2.28 training have been observed as of this commit.
