# LLM_CHA v0.2.32.4 — Experimental Purpose-Conditioned SFT

This branch adds a **real PyTorch SFT training pipeline** using `LanguageModel.load_checkpoint`, existing BPE tokenizer and the short prompt format adopted after v0.2.32.3 ablation.

## Contents
- `prepare_purpose_sft_v02324.py`: hand-written sample templates for learning/development/troubleshooting/casual and sequential planning, train/validation/test split by disjoint topics, and legacy-format replay cases.
- `train_purpose_sft_v02324.py`: response-token-only cross entropy (prompt tokens ignored), AdamW, differential LM-head LR, gradient clipping, replay loss, best validation NLL checkpoint.
- `evaluate_purpose_sft_v02324.py`: frozen base versus trained checkpoint on held-out topics and old-format replay prompts (free generation, greedy decoding).
- `test_purpose_sft_v02324.py`: masks, topics, context limits and forward/loss checks.

## Warnings
This is a deliberately **small, templated demonstration dataset** (train 36, val 18, test 18). Topic labels do not overlap, but the **sentence and answer templates do overlap**; therefore test results cannot establish general-purpose semantic generalization. The same four simple legacy replay prompts are used in the training penalty and later shown in replay evaluation; this is **training replay diagnostic only**, NOT independent retention holdout. It does not automatically test the full preexisting chat function distribution.

`test` topics are excluded from train and validation for checkpoint selection. Do not repeatedly optimize on test output and call it an untouched held-out test.

Checkpoint `model/model-llm-cha-purpose-sft-v02324.pt` is distinct from the base checkpoint. Model dimension, vocab size and context-length compatibility are validated. Oversized rows fail rather than silently truncate. Training may be slow due to per-example optimizer updates and multiple full forward passes.

## Windows commands

```powershell
git fetch origin
git switch v0.2.32.4
git pull origin v0.2.32.4

python -m unittest -v test_purpose_sft_v02324.py
python prepare_purpose_sft_v02324.py

python train_purpose_sft_v02324.py `
  --model model/model-llm-cha-response-quality-v0221.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --epochs 8

python evaluate_purpose_sft_v02324.py `
  --base model/model-llm-cha-response-quality-v0221.pt `
  --trained model/model-llm-cha-purpose-sft-v02324.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

## Interpreting results
- Report train/validation NLL and legacy replay NLL separately.
- Compare generated responses **rather than loss alone**. Check topic/goal relevance, Japanese fluency, variation, unsupported answers and unlearning.
- Before using the model in production, expand data substantially, create independently authored test utterances/answers, and establish a separate broad legacy competence suite.
- The SFT checkpoint is **not automatically integrated into chat.py** and trained formats do not automatically transfer to the long Full DSS prompt. Short-form inference is the intended first test.

## Next
Assess whether the training improves free generation for held-out topics without destroying old chat behavior. If it fails, revise corpus diversity, response completion supervision and stability replay before implementing a generation-quality gate.
