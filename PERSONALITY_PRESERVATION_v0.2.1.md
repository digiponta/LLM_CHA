# LLM_CHA v0.2.1 — Personality Preservation Experiment

Development branch `v0.2.1`, based on `v0.1.0`.

## Goal

Test whether identity replay can preserve the v9.4 Nagato identity and basic conversation responses while gaining general conversation ability from RealPersonaChat.

Baseline observations: RealPersonaChat-only v0.2.0 returned "未学習です" for "あなたは誰ですか" while v9.4 returned "長門有希。"; it also gave unsuitable answers to thanks and requests for a story.

## Commands

```powershell
git fetch origin
git switch --track origin/v0.2.1
python -m unittest -v test_conversation_replay_v021.py
python prepare_conversation_replay_v021.py --source data/realpersonachat/rpc_train.jsonl --output data/realpersonachat_replay --max-rpc 20000 --replay-factor 300
python train_conversation_replay_v021.py --dry-run
python train_conversation_replay_v021.py
```

The script passes `--anchor-data` and `--anchor-weight` to the existing SFT implementation, because ordinary input JSONL pairs are deduplicated by that trainer.

Output checkpoint: `model/model-llm-cha-rpc-replay-v021.pt`.

Compare:

```powershell
python chat.py --model ../LLM_TRY/model/model-llm-try-nagato-chat-v94.pt --tokenizer ../LLM_TRY/model/tokenizer-v0.7-bpe.json --temperature 0
python chat.py --model model/model-llm-cha-rpc-v020.pt --tokenizer ../LLM_TRY/model/tokenizer-v0.7-bpe.json --temperature 0
python chat.py --model model/model-llm-cha-rpc-replay-v021.pt --tokenizer ../LLM_TRY/model/tokenizer-v0.7-bpe.json --temperature 0
```

Use the same questions: こんにちは / 今日は少し疲れました / 何か面白い話をして / 最近は本を読んでいます / どんな本が好き？ / ありがとう / CPUとは / GPUはなぜ高速なの？ / あなたは誰ですか.

## Acceptance checks

- Identity query must return `長門有希。`.
- Thanks and greeting should match their speech acts.
- Do not accept a checkpoint merely because validation loss decreases.
- Test the original Semantic Memory / Truth-State / Unknown Gate / `/sleep` paths.
- The anchor evaluation file is a *training-replay diagnostic*, not an independent test set. Genuine held-out evaluation must use unseen dialogues and non-trained phrasings.
- The prior conversation converter flattens multiple turns into the user field; dialogue-context alignment remains a known limitation.

## Status

Dataset preparation script, training launcher, tests are committed. Local GPU training and regression execution are not performed by this GitHub update. Base checkpoint is never overwritten. RealPersonaChat retains the source CC BY-SA 4.0 license.
