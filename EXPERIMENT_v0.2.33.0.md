# LLM_CHA v0.2.33.0 — Internalization Failure Diagnostics

## Research question
Why did the v0.2.32.8/9 expansion training improve training NLL but fail to produce useful purpose-aligned free responses?

This version diagnoses **token prediction**, not semantic transfer success. It compares Base / Original SFT / Expanded SFT, all at the same supplied training prompts and teacher replies.

## Measurements
- First-token top-1 accuracy, rank and model probability of the teacher's first token.
- Token-by-token teacher-forced cross entropy and first five token losses.
- Greedy free generation with no answer prefix.
- Greedy generation after supplying 25% of the reference answer as a prefix.

The token-level metrics are calculated on **training examples**; they can expose a first-token bottleneck, but **cannot measure generalization**. The string prefix experiment is approximate because decoding/re-encoding BPE may shift token boundaries. Do not use it to claim a controlled exact-token continuation; future work can implement continuation with token IDs directly.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.0
git pull origin v0.2.33.0
python -m unittest -v test_internalization_diagnostics_v02330.py

python diagnose_internalization_v02330.py `
  --expansion data/semantic_expansion_v02328.jsonl `
  --base model/model-llm-cha-response-quality-v0221.pt `
  --original model/model-llm-cha-memory-original-v02328.pt `
  --expanded model/model-llm-cha-memory-expanded-v02328.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

Output: `results/internalization_diagnostics_v02330.json`.

## Interpreting outcomes
If teacher-forced NLL drops but the first token remains very unlikely, prioritize response initiation / curriculum training. If first tokens become accurate but prefixes fail, diagnose continuation/repetition/semantic drift. If prefix completion works but raw free generation fails, investigate initiation and exposure bias. If all cases fail, rethink supervision density/model capacity and conditional bridge. Each case calls for external *held-out* free-generation evaluation before any INTERNALIZED promotion.

This branch **does not** implement semantic projection or student distillation yet; they are proposals contingent on diagnostic evidence. It does not run background work, switch chat.py to candidates or alter Semantic Memory promotion state.
