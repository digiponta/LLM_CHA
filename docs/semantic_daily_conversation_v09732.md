# LLM_CHA v0.9.7.32 — Semantic-aware Daily Conversation SFT

The v0.9.7.31 report showed **0/12** held-out exact matches and
**0/12** coarse strategy-keyword matches following v0.9.7.30 SFT.
This iteration strengthens supervised examples for nine groups:
POSITIVE, DISAPPOINTMENT, SADNESS, FATIGUE, GRATITUDE, UNCERTAINTY,
NEGATED_POSITIVE, NEGATED_SADNESS, and MIXED.

- Keep the original **12 holdout items** evaluation-only.
- Add **new training examples** distinct from those inputs.
- Add extra held-out diagnostic items across the nine categories.
- Maintain per-sample semantic tags (emotion and response strategy).
- Train from the **original protected checkpoint** for a controlled
  comparison against v0.9.7.30, not from the already tuned model.
- Use the same completion-only SFT mechanism and protected QA replay.
- Write a new, separate checkpoint; no runtime answer-route change.
- Default to dry-run; only `--train` permits weight updates.

**Important limitation:** Because the earlier 12 holdout results have
already been inspected and informed this design, they are now a
development evaluation set, not a truly independent final test.
The new evaluation examples were also authored during development,
so additional untouched future examples are required for any final
generalization claim. Synthetic examples are not substitutes for
real human conversations.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.32
python -m unittest -v test_semantic_daily_conversation_v09732.py test_daily_conversation_sft_v09730.py
python semantic_daily_conversation_v09732.py

python train_semantic_daily_sft_v09732.py `
  --model model/model-llm-try-nagato-chat-v94.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json

python train_semantic_daily_sft_v09732.py `
  --model model/model-llm-try-nagato-chat-v94.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output model/model-llm-cha-semantic-daily-v09732-experimental.pt `
  --epochs 3 --lr 0.00002 --replay 3 --train
```

Check training loss and before/after held-out loss; do not equate
lower NLL with a meaningful emotion classification improvement.
Next evaluate all held-out answers, including negation and mixed
emotion, against v0.9.7.30 with a human-readability and intent audit.
