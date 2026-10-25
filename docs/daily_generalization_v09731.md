# LLM_CHA v0.9.7.31 — Daily Conversation Holdout Generation Evaluation

This branch compares the original baseline checkpoint with the isolated
v0.9.7.30 SFT checkpoint. It does **not** train, modify model weights,
change normal chat routing, or promote Semantic Memory.

Two models are prompted under the same generation settings for:
- **12 held-out samples** from v0.9.7.28 (2 per category).
- **7 challenge probes** covering negation, mixed emotion, irony,
  Nagato identity and greetings.

Metrics: exact target string match and a coarse response-strategy keyword
proxy, plus generated text and confidence per model. Neither metric is a
reliable substitute for human assessment of meaning, coherence, empathy,
safety or overfitting; all rows are marked for manual review.
The challenge probes have no reference completions, so they do not
contribute to exact-match totals.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.31
python -m unittest -v test_daily_generalization_v09731.py test_daily_conversation_sft_v09730.py
python evaluate_daily_generalization_v09731.py `
  --baseline model/model-llm-try-nagato-chat-v94.pt `
  --experimental model/model-llm-cha-daily-sft-v09730-experimental.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output results/daily_generalization_v09731.json
```

The output JSON includes all 19 paired examples and a compact summary.
Output file collision is rejected rather than overwritten.
Inspect the report's `rows` for errors where an optimistic/negative
reply is inappropriate (e.g. negation or irony). Check identity retention
and compare unseen paraphrases against the untouched baseline.
