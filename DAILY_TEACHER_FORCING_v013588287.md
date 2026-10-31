# v0.13.58.82.87 — Teacher-forced Token Diagnosis

Three **seen training** prompts (おはよう / 雑談しよう / 相談がある) are evaluated using Model A and fine-tuned Model B. Each reference-answer token, **including EOS**, is scored under teacher forcing: probability, rank, NLL; then greedy tokens are generated from the same chat prompt and the first divergence index is found. This does **not** change the models or the independent five-question holdout.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.87-teacher-forced-analysis
python -m unittest -v test_daily_teacher_forcing_v013588287.py test_daily_decode_v013588286.py

python diagnose_daily_teacher_forcing_v013588287.py `
 --base model/model-gpu-v1.6.2-online.pt `
 --candidate model/daily-sft-candidate-v013588284.pt `
 --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json
```

Output: `results/daily_teacher_forcing_v013588287.json`. Compare first-divergence index, mean answer NLL, and token ranks. `token_details` includes the full per-token trace. Note that a first-divergence index may count EOS and is in **token positions, not characters**. This experiment cannot by itself distinguish data quantity from model architecture or prove a model size limit.
