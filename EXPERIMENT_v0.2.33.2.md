# LLM_CHA v0.2.33.2 — Semantic-to-Generation Bridge (experimental)

The purpose of this experiment is to test whether externally supplied semantic structure can directly alter LLM_CHA's next-token logits through a trainable hidden-state projection, instead of exclusively relying on text prompts.

```text
DSS canonical labels (Topic / Purpose / Relation)
       → deterministic 64-dimensional signed feature hash
       → learned 64→d_model projection
       → addition to final normalized Transformer hidden states
       → frozen language-model head
       → token probabilities and generation
```

The implementation uses `model.forward_hidden` and `model.lm_head`. The *entire original LanguageModel remains frozen*, with only a zero-initialized linear projection trained on the same approved Semantic Memory response pairs.

The hashed features are a lightweight placeholder, **not pretrained LLM_SEM semantic embeddings**. A fixed topic/purpose/relationship label can be assigned externally. Inference with the correct semantic vector therefore **does not demonstrate DSS-free internalization**, and a conditioned response can still be incoherent.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.2
git pull origin v0.2.33.2

python -m unittest -v test_semantic_generation_bridge_v02332.py

python semantic_generation_bridge_v02332.py train `
  --expansion data/semantic_expansion_v02328.jsonl `
  --base model/model-llm-cha-response-quality-v0221.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --epochs 12

python semantic_generation_bridge_v02332.py evaluate `
  --base model/model-llm-cha-response-quality-v0221.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

Outputs: `model/semantic-bridge-v02332.pt` and `results/semantic_bridge_eval_v02332.json`.

## Evaluation method and known limitations

- Evaluate **zero semantic** versus **teacher semantic**, both with raw and Short prompt forms, using identical greedy generation lengths.
- Existing exploratory v0.2.32.7 prompts are reused, so this is a **pilot, not an untouched holdout**.
- The current `evaluate` path constructs semantic vectors using topic/purpose but omits relation, including SEQUENTIAL. This is a limited ablation, not a full fidelity relation-conditioned evaluation.
- Compare fluency, goal fidelity and factual correctness manually; NLL alone does not establish semantic ability.
- A single additive global vector is a very small intervention; it may bias token probabilities without controlling multi-sentence meaning. It may also harm retained behaviors. No automatic promotion to INTERNALIZED or checkpoint switch is performed.
- Next: compare against a parameter-matched nonsemantic control and train a *student semantic predictor from raw user text* to eliminate external DSS at inference if a semantic bridge proves useful.
