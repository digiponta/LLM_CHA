# v0.13.58.82.84 — Small Daily Conversation Fine-Tuning Experiment

Goal: test whether **limited conversational supervision** improves natural answers without confusing surface acceptance with model learning. The original 8.96M-parameter model stays the control. No automatic production checkpoint promotion. This release is training-data preparation, holdout screening, and a command recipe; **training has not been run on the user's GPU**.

Training: 60 manually authored short Japanese user/assistant pairs in `data/daily_sft_train_v013588284.jsonl`, formatted for the existing `online_train.py` with `source=chat-manual`. The v0.83 five-question evaluation set is excluded from training, including exact expected answers. Exact-match isolation is tested, but semantic overlap may remain. Treat this as a small exploratory experiment, not an independent publication benchmark.

Windows PowerShell:

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.84-daily-sft-ab

python -m unittest -v test_daily_sft_isolation_v013588284.py test_daily_conversation_eval_v013588283.py
python check_daily_sft_isolation_v013588284.py

# Keep chat.py closed while conducting the experiment.
# Use the current production checkpoint as immutable base, separate paths for outputs.
python online_train.py `
  --chat-data data/daily_sft_train_v013588284.jsonl `
  --base-model model/model-gpu-v1.6.2-online.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json `
  --output model/daily-sft-candidate-v013588284.pt `
  --state results/daily-sft-state-v013588284.json `
  --epochs 2 `
  --learning-rate 1e-5 `
  --replay-ratio 1.0
```

The default replay and stability paths used by online_train.py must exist and should be inspected before training. Do not change the existing production model path. If the trainer reports NO_NEW_PAIRS or configuration errors, do not claim that training succeeded.

Compare actual output with the same tokenizer, decoding settings, and five untouched evaluation questions:

```powershell
python chat.py --model model/model-gpu-v1.6.2-online.pt
# record the five holdout questions /exit

python chat.py --model model/daily-sft-candidate-v013588284.pt
# record the identical five holdout questions /exit
```

Use the existing `daily_conversation_eval_v013588283.py` to record **actual** displayed responses and rejected candidates in separate observation JSON files for each checkpoint, and compare `surface_usable` and `fallback`. A human must separately judge whether each output genuinely answers the prompt, not merely passes a gate. Finally repeat the registered `閃亜鉛鉱` three-question check for knowledge retention. Do not merge the candidate checkpoint into production until these comparisons are reviewed.
