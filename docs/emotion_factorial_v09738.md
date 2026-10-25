# v0.9.7.38 — Four-arm matched condition SFT

Ablation v0.9.7.37 found response collapse. This branch conducts a
**factorial controlled training experiment** from the SAME original
v9.4 checkpoint: plain / emotion-only / strategy-only / both.
Each arm uses the same 73 training utterances, 30 development holdouts,
same 9 protected QA replay items, seed, epochs and optimizer. Only
input prefixes change. Output checkpoints are independent and existing
files are never overwritten.

This is opt-in training and does NOT touch chat.py, Semantic Memory,
or original checkpoint.

## Pull and test
```powershell
git fetch origin
git switch --track origin/v0.9.7.38
python -m unittest -v test_emotion_factorial_v09738.py
```

## Train all arms (PowerShell)
```powershell
$base = "model/model-llm-try-nagato-chat-v94.pt"
$tok = "model/tokenizer-v0.7-bpe.json"
foreach ($arm in @("plain","emotion","strategy","both")) {
  python train_emotion_factorial_v09738.py `
    --arm $arm --model $base --tokenizer $tok `
    --output "model/model-llm-cha-factorial-v09738-$arm.pt" `
    --epochs 3 --lr 0.00002 --replay 3 --seed 42 --train
  if ($LASTEXITCODE -ne 0) { throw "Training failed: $arm" }
}
```

## Evaluate the 37 existing development cases
```powershell
python evaluate_emotion_factorial_v09738.py `
  --plain model/model-llm-cha-factorial-v09738-plain.pt `
  --emotion model/model-llm-cha-factorial-v09738-emotion.pt `
  --strategy model/model-llm-cha-factorial-v09738-strategy.pt `
  --both model/model-llm-cha-factorial-v09738-both.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output results/emotion_factorial_v09738.json
```

The result contains 37 x 4 = 148 completions and descriptive
statistics. **Exact match is not semantic accuracy.** These holdouts
have been inspected repeatedly, so they are *development evaluation*,
not independent generalization evidence. No model is automatically
promoted. Compare actual output text and category consistency before
considering a separate, fresh final holdout.

The v0.9.7.35 BOTH prompt includes an additional DIALOGUE_ACT marker;
v0.9.7.38 removes that marker consistently so the four-arm factorial
comparison isolates only the two stated factors. It must NOT be
presented as an exact replication of v0.9.7.35.
