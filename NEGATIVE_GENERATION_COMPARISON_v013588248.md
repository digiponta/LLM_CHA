# v0.13.58.82.48: Negative-only candidate generation comparison

Compare the existing baseline checkpoint with the three-step negative-only experimental candidate. Every probe is generated under identical **greedy** decoding and fixed seed, with no automatic checkpoint promotion or modification.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.48-negative-generation-eval
python -m unittest -v test_negative_generation_comparison_v013588248.py test_negative_only_experiment_v013588247.py
python compare_negative_generation_v013588248.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --candidate results/negative_only_v013588247_steps3.candidate.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json `
  --negative-data data/negative_teacher_signals_v013588244.jsonl `
  --output results/negative_generation_eval_v013588248.json
Get-Content results/negative_generation_eval_v013588248.json -Encoding UTF8
```

Reports the before/after candidate text, the observed negative NLL for each negative example, and exact repeats. Also probes CPU, GPU and an explanatory cosmos query. This is **generation-level diagnostic only**, not evidence-gate scoring or independent holdout. The actual GUI evidence-conditioned prompt includes a Wikipedia excerpt and differs from the standalone chat-format prompt used by this tool. A later version should replay the exact encode_request prompt for reliable GUI-level conclusions. The candidate remains experimental; nothing changes the active GUI checkpoint.
