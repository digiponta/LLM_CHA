# LLM_CHA v0.2.33.13 — Core Functional Verification

After the v0.2.33.12 checkpoint audit confirmed position embeddings and causal attention were enabled, this experiment checks **actual function**, rather than checkpoint config alone.

## Checks

- **Causal isolation**: changing only the final token must leave all earlier-position logits invariant.
- **Full forward vs generation**: greedy `generate` with repetition penalty disabled must match `model(input).argmax` for the next token. Current implementation recomputes the context rather than using a KV cache; this is a parity check, *not* incremental-cache verification.
- **Gradient flow**: verify nonzero finite gradients at embedding, Q/K/V and LM head for a response-only copy objective.
- **Checkpoint roundtrip**: save the model temporarily, reload, and compare logits.
- **Tiny one-sample overfit**: train *only an in-memory loaded model* on a single copy pair, deliberately without replay, until memorization becomes possible. Record teacher top-1, NLL and exact greedy copy. Success demonstrates the mechanism can memorize one example, **not generalization**.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.13
git pull origin v0.2.33.13
python -m unittest -v test_llm_core_functional_v023313.py
python verify_llm_core_functional_v023313.py --steps 150
```

Output: `results/core_functional_verification_v023313.json`.

The original checkpoint file is not overwritten. New model parameters from the one-sample overfit are not saved; the results are diagnostics only. DSS, Semantic Memory, Semantic Bridge and chat routing remain unchanged.

Do not infer that passing unit tests guarantees meaningful language generation. If one-sample memorization cannot be achieved, inspect training masks, logits and losses more closely before further Semantic Bridge experiments.
