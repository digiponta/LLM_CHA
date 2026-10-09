# v0.2.32.9 — Three-model Semantic Expansion Transfer Evaluation

**Goal:** compare frozen Base, Original-only SFT (2 teacher examples), and Expanded SFT (6 reviewed examples) under identical generation conditions. Focus on previously untrained utterances, not Train NLL.

## Run in Windows PowerShell

```powershell
git fetch origin
git switch v0.2.32.9
git pull origin v0.2.32.9
python -m unittest -v test_semantic_expansion_transfer_v02329.py

python evaluate_semantic_expansion_transfer_v02329.py `
  --expansion data/semantic_expansion_v02328.jsonl `
  --base model/model-llm-cha-response-quality-v0221.pt `
  --original model/model-llm-cha-memory-original-v02328.pt `
  --expanded model/model-llm-cha-memory-expanded-v02328.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

Output: `results/semantic_expansion_transfer_v02329.json` with raw user-only prompts and Short prompts with externally supplied Topic/Purpose, same token budget and greedy decoding. The legacy set uses raw prompts. Review every free-generation response for relevance, Japanese fluency, truthfulness, and retention, with particular attention to unseen paraphrases and previously untrained legacy questions.

**Crucial caveat:** Expanded was trained with six pairs for eight epochs (48 optimizer updates), versus Original with two pairs for eight epochs (16 updates). Lower NLL could reflect *more updates*, not only paraphrase variety. These exploratory holdouts were already used in v0.2.32.7 and are **not an independent sealed final test**. They are excluded from training but repeated inspection weakens claims of unbiased model selection. Do not mark INTERNALIZED from this experiment.

## Equal-update follow-up (no new training logic needed)

Run `train_semantic_expansion_v02328.py --epochs 24` with **fresh output paths** for both branches if you need an Original model with 48 training updates. This will also train Expanded for 144 updates; only the Original-24 checkpoint and existing Expanded-8 checkpoint should be compared in an update-matched analysis. Keep the same base, seed, tokenizer and LR/replay settings.

Example:

```powershell
python train_semantic_expansion_v02328.py `
  --epochs 24 `
  --original-out model/model-llm-cha-original-24epoch-v02329.pt `
  --expanded-out model/model-llm-cha-expanded-24epoch-v02329.pt `
  --report results/semantic_expansion_train_24epoch_v02329.json

python evaluate_semantic_expansion_transfer_v02329.py `
  --original model/model-llm-cha-original-24epoch-v02329.pt `
  --expanded model/model-llm-cha-memory-expanded-v02328.pt `
  --out results/semantic_expansion_transfer_equal_updates_v02329.json
```

This rough matching controls the **number** of updates (48 vs 48), not every factor (sample ordering, repetition, parameter trajectory). No checkpoint is overwritten, and still no independent validation of purpose recognition without DSS. The `raw` output condition tests direct generation from a user sentence; proof of reliable DSS-free interaction requires larger precommitted topic/purpose coverage and live conversation regressions.
