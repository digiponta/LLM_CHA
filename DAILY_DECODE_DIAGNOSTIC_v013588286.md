# v0.13.58.82.86 — Generation Decoding Diagnosis

No new training. Analyze three **seen** training questions using the original Model A and fine-tuned Model B under two decode strategies. Also report the probability and rank of the first reference-answer token at the model's actual prompt boundary. Models are loaded read-only; no checkpoint promotion.

Windows:

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.86-decode-diagnostics

python -m unittest -v test_daily_decode_v013588286.py test_daily_sft_binding_v013588285.py

python diagnose_daily_decode_v013588286.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --candidate model/daily-sft-candidate-v013588284.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json
```

The output is `results/daily_decode_diagnostic_v013588286.json`; compare first-token probability/rank and both generated strings for each question.

Interpretation:
- Improved first-token rank but broken continued generation suggests errors later in generation or insufficient sequence-level learning.
- Poor first-token rank even for seen questions suggests training/format/context mismatch or insufficient learning.
- Greedy more coherent than sampled suggests decoding noise is a factor; neither alone proves model capacity.
- This tool measures **first** target-token probability only, not full teacher-forced NLL. The two decoding settings are fixed to temperature 0 and 0.45, top-k 20, penalty 1.0; they're diagnostic, not necessarily the whole chat.py policy.
- Do not reuse the v0.83 five-question holdout for training. Do not compare losses from different underlying datasets as if they were identical.
