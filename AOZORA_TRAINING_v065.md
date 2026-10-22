# LLM_CHA v0.6.5 — Aozora GPU continued pretraining (experimental)

Training is **optional**. The v0.6.4 ingest stage generated 440 chunks from
two works (789 = 吾輩は猫である, 1567 = 走れメロス). This stage fine-tunes
a new model checkpoint without changing the base checkpoint, existing
Semantic Memory, `/sleep`, or existing chat runtime.

## Windows / RTX 3070 Ti

```powershell
git fetch origin
git switch v0.6.5
git pull --ff-only origin v0.6.5
python -m unittest -v test_train_aozora_continued_v065.py
python train_aozora_continued_v065.py --dry-run
python train_aozora_continued_v065.py --epochs 2 --batch-size 4 --block-size 128 --learning-rate 5e-6
```

Defaults use:
- JSONL: `data/aozora_v064/aozora_semantic_corpus.jsonl`
- Tokenizer: `model/tokenizer-v0.7-bpe.json`
- Base: `model/model-llm-try-nagato-chat-v94.pt`
- Output: `model/model-llm-cha-aozora-v065.pt`
- Report: `results/aozora_training_v065.json`

Adjust `--base-model` to an existing model checkpoint with a matching
tokenizer; a missing file raises FileNotFoundError. The output checkpoint
must not already exist. Keep source checkpoint copies.

## Evaluation method and limits

- Whole-work holdout: *走れメロス* (1567) is not used for training.
- *吾輩は猫である* (789) is used for training.
- Before/after next-token loss measured on both partitions.
- Validation is only **one held-out work** and therefore not sufficient
  to claim general Japanese quality improvements.
- `persona_regression_verified` is false; evaluate persona conversational
  replies and memory behavior independently before promoting a model.
- Data is fiction: retain `EXTERNAL_UNVERIFIED` and do not assert story
  content as factual memories.
- Loss improvement alone is not evidence of dialogue quality or style transfer.
- Running multiple times needs a distinct `--output` and `--report`.
- Python packages required: `torch`, `tokenizers`.

## Use a trained model for an isolated experiment

```powershell
python chat.py --model model/model-llm-cha-aozora-v065.pt --tokenizer model/tokenizer-v0.7-bpe.json
```

Check `results/aozora_training_v065.json` before trying the experimental
checkpoint. Do not replace any stable model by default.
