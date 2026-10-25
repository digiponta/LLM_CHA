# LLM_CHA v0.9.7.30 — Daily Conversation SFT (opt-in experiment)

This branch implements an **optional, isolated GPU/CPU fine-tuning experiment**
for the 30 daily conversation examples from v0.9.7.28. The 12 holdout
examples are used for **evaluation only**, never for gradient updates.

The trainer reads the same `model.py` checkpoint format and
`tokenizer_bpe.py` tokenizer as the current runtime. It creates a
separate experimental model; the original checkpoint is not overwritten.

## Design

- Completion-only next-token cross-entropy; mask all `人: ...\nAI: `
  prompt token targets.
- 30 synthetic daily conversation training pairs plus repeated **protected
  Nagato identity QA** to reduce forgetting.
- Short default trial: 3 epochs; AdamW learning rate 2e-5; gradient clipping 1.0.
- Before/after: daily holdout loss, protected QA loss and a small set of
  generated responses.
- Does not silently change chat.py's startup model, modify Semantic Memory,
  approve facts, or automatically accept output.
- CLI is dry-run by default; actual training requires `--train`.
- If the chosen output file already exists or resolves to the source, it
  fails closed instead of overwriting anything.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.30
python -m unittest -v test_daily_conversation_sft_v09730.py test_daily_conversation_foundation_v09728.py
```

Determine the actual baseline checkpoint and tokenizer paths from your
successful `python chat.py` startup, and pass them explicitly. Example,
**only if those paths exist**:

```powershell
python train_daily_conversation_sft_v09730.py `
  --model model/model-llm-try-nagato-chat-v94.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

This first command is a dry-run with baseline diagnostics.

To run the separate experiment (explicit opt-in):

```powershell
python train_daily_conversation_sft_v09730.py `
  --model model/model-llm-try-nagato-chat-v94.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output model/model-llm-cha-daily-sft-v09730-experimental.pt `
  --epochs 3 --lr 0.00002 --replay 3 --train
```

If chat.py loads the model/tokenizer from a sibling repository, use those
absolute or relative paths instead.

Compare before/after outputs and protected QA loss; a lower holdout NLL
alone does not establish robust dialogue. Future work: sentiment-stratified
held-out generations, negation/irony cases, multiple random seeds, and
actual replay samples from proven-good conversations.

**Limitations:** The three protected questions are minimal, not a
comprehensive forgetting test. Train/holdout phrases are synthetic and
closely related. The model may overfit; do not deploy this checkpoint
without a separate acceptance gate.
