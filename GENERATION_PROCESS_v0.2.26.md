# LLM_CHA v0.2.26 — Generation Process Analysis

Diagnostic-only branch. No additional training, runtime gate changes or overwriting prior checkpoints.

Comparisons: `model-llm-cha-context-weighted-v0224.pt` vs `model-llm-cha-context-generalization-v0225.pt`. Use the same pretrained tokenizer and the same 6 selected training contexts / 6 unseen contexts.

Measures:
- Greedy free generation and complete per-step top-8 token probabilities, selected token and EOS probability, with repetition penalty 1.15 (as the v0.2.16 diagnostic).
- Teacher-forced, normalized assistant NLL for three generic acknowledgment answers and a topic-specific reference. `reference_vs_short_ack_nll_gain = NLL("そう。") - NLL(reference)`. **Positive** means the full reference has better per-token average log likelihood; this is not the probability that the reference is chosen in free generation.
- Full JSON for manual review of readability, grammaticality and grounding. No automated metric in this script proves Japanese fluency.

PowerShell:
```powershell
git fetch origin
git switch --track origin/v0.2.26
python -m unittest -v test_generation_process_v0226.py
python diagnose_generation_process_v0226.py
```

Output: `results/generation_process_v0226.json`.

Interpretation: if topical reference is relatively likely but Greedy keeps selecting short acknowledgments, inspect the **first few token logits** and EOS trajectory. If specific-topic tokens never enter the top-8, simple reranking cannot recover them. If probabilities move toward relevant tokens in v0.2.25 but text still collapses, investigate autoregressive exposure bias, dataset structure, tokenizer segmentation and decoding distribution next. Compare unseen topics before any adoption. Current synthetic cases are not a representative unbiased corpus; no statistical claims.
