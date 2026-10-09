# LLM_CHA v0.2.12 — Diverse Dialogue Generalization Pilot

Goal: investigate whether a larger, naturally varied RealPersonaChat dataset improves conversation *generation* across new topics. This is a GPU training experiment; no trained checkpoint is committed. The v0.2.11 six-dialogue 30× repetition is **not** used as the main data source.

## Pipeline

1. Rebuild the v0.2.4 dataset from the RealPersonaChat dialogue files with `--max-dialogues 0` to include all available dialogues. The existing v0.2.4 converter uses dialogue-ID-based train/val/test partitions.
2. Filter bad/generic reply targets from the **train data**, and independently filter evaluation data without moving any row into train. A simple lexical topic holdout excludes photo/garden mentions from train and collects those examples from val in `topic_holdout.jsonl`. This is NOT a rigorous semantic topic split, and underlying train text may still convey similar concepts. Inspect the manifest.
3. Train from **v0.2.8**, not v0.2.11, at low learning rates using up to 50k diverse train pairs. v0.2.8 persona anchors remain a separate replay source.
4. Keep train, general validation, topic holdout and test separate; compare all checkpoints under equal inference parameters.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.2.12
python -m unittest -v test_generalization_v0212.py test_dialogue_sft_v0211.py
python prepare_multiturn_v024.py --max-dialogues 0 --history-turns 2
python prepare_generalization_v0212.py --max-train 50000
python train_generalization_v0212.py --dry-run
python train_generalization_v0212.py
```

Expected output checkpoint:

`model/model-llm-cha-generalization-v0212.pt`

## Inference

```powershell
python chat.py --model model/model-llm-cha-generalization-v0212.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --probe-count 3 --temperature 0 --show-context --show-dialogue-state --show-conversation-diagnostics --show-candidate-ranking
```

Try `最近、小説にはまっています`, `SFです`, `その話、続けて`, then `/reset`; test `最近、写真を撮っています`, `夜景です`, `その話、続けて`. Compare with v0.2.8 and v0.2.11 in identical settings. The latter conversations are *illustrative*, not sufficient to certify cross-topic generalization.

## Evaluation requirements

- Same held-out dataset (with assistant-only NLL) for checkpoint comparisons; checkpoint losses from their different original training sets are **not directly comparable**.
- Score user-topic relevance, meaningful continuation, generic reply rate, malformed text, question repetition, and accepted-but-bad response rate. Include unseen human-authored conversations.
- `あなたは誰ですか` with character mode uses deterministic intent routing; it does not prove that weights retain persona knowledge.
- Check CPU canonical definition, unknown GPU query, Truth-State warnings, Semantic Memory, and `/sleep` regressions separately.
- SFT on real-world conversations carries data-source license and attribution obligations; keep the existing RealPersonaChat CC BY-SA 4.0 attribution and check compliance before redistribution.

## Limitations

An 8.96M-parameter model with limited pretraining may still lack fluency, regardless of the SFT volume. The source corpus, filtering, and training distribution matter more than a single checkpoint loss. The lexical topic holdout has limited coverage and is not guaranteed free from semantic leakage. **No claim of improved quality should be made until local GPU results and held-out human assessments are available.**
