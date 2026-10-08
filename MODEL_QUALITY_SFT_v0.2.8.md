# LLM_CHA v0.2.8 — Model-Side Quality SFT Pilot

This branch adds an experimental training pipeline for reducing bland replies, without modifying the v0.2.1/v0.2.4 checkpoints, Semantic Memory, Truth-State, or conversation gates.

## Design

1. Read the **training split only** from v0.2.4's role-aligned RealPersonaChat JSONL.
2. Drop exact generic targets (e.g. `そうですね`, `はい`) and replies under 12 characters. Randomly cap the pilot to 25,000 samples. This is a *biased length/quality proxy*, **not** verified semantic quality: filtering can discard good brief replies and does not assure useful long replies.
3. Convert character anchors into the `人:`-prefixed preformatted format, then replay using the existing SFT trainer's `--anchor-data` pathway. This avoids prepending `人:` twice and retains the identity.
4. Fine-tune from `model-llm-cha-rpc-replay-v021.pt` with lower learning rates. Save to a separate checkpoint.

## Run locally (PowerShell)

```powershell
git fetch origin
git switch --track origin/v0.2.8

python -m unittest -v test_quality_sft_v028.py test_multiturn_v024.py test_conversation_quality_v027.py
python prepare_quality_sft_v028.py --max-train 25000 --min-answer-chars 12
python train_quality_sft_v028.py --dry-run
python train_quality_sft_v028.py
```

If zero rows survive filtering, regenerate multi-turn data with more source dialogues:

```powershell
python prepare_multiturn_v024.py --max-dialogues 5000 --history-turns 2
python prepare_quality_sft_v028.py --max-train 25000
```

## Evaluate

```powershell
python chat.py --model model/model-llm-cha-quality-v028.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --temperature 0 --show-context --show-conversation-diagnostics
```

Compare **identical inputs** under identical settings against:
- `model/model-llm-cha-rpc-replay-v021.pt`
- `model/model-llm-cha-multiturn-v024.pt`

Suggested sequence: `最近、小説にはまっています`, `SFです`, `その話、続けて`, `/reset`, `その話、続けて`, `あなたは誰ですか`, `お名前を伺えますか`, `CPUとは`, `GPUの並列処理が速い理由を説明して`.

Use an independent held-out validation split for loss, and human ratings for topical relevance, factuality, character consistency, and generic response fraction. **Do not** rely on decreasing loss alone. Character identity and basic replies may be router-generated rather than proof of learned generalization. Verify full Semantic Memory / Truth-State / /sleep regressions before release.

Status: committed to GitHub; CPU tests, GPU training and runtime improvements **not yet executed or verified**.
