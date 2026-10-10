# LLM_CHA v0.2.33.26 — Adaptive Pointer Gate & Length Generalization

## Previous measured findings

v0.2.33.25 (single seed):
- Pointer-only: Test 21/40; unseen task IDs 8/40; long 0/40.
- Hybrid: Test 32/40; unseen task IDs 0/40; long 0/40.
- Both selected epoch 2 using short-known-ID validation loss.

## New experiment

Use the original v0.2.33.20 token-copy checkpoint as a **frozen backbone**. Compare:
- `pointer`: learned Q/K source-position distribution and trainable EOS logit.
- `hybrid`: source-position distribution blended with frozen LM distribution, gated by hidden state.
- `adaptive`: same blend, but the gate receives final hidden state and three confidence features: frozen-LM max probability, pointer max probability, and overlap of LM/pointer vocabulary distributions.

Every arm uses the **same three-stage curriculum**, source examples and optimizer steps:
1. One training pass on 200 short sequences (length 2–8).
2. One pass on 200 length-diverse sequences (2–18).
3. One additional pass over the same length-diverse sequences.

Each stage includes source-position supervision for every copied token plus EOS position. **In inference, no gold copy position or gold output length is provided.**

The short-known-ID validation set alone selects the best stage; this is deliberately reported as a limitation because it may prefer shorter-series proficiency. Evaluate on disjoint:
- `test`: short known IDs;
- `long`: length 12–18, known IDs;
- `unseen_token_ids`: source IDs 72–87;
- `mixed_ids`: 8–87 mixture;
- `novel_extra`: source IDs 88–103.

For each group, record free-generation exact copy **including EOS**, teacher-forced pointer position accuracy and correct-EOS position accuracy. Student remains frozen; only new heads are saved. Evaluation code refuses overwrite.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.26
git pull origin v0.2.33.26
python -m py_compile adaptive_pointer_length_v023326.py
python -m unittest -v test_adaptive_pointer_length_v023326.py
python adaptive_pointer_length_v023326.py
```

Outputs: `results/adaptive_pointer_length_v023326.json`, plus `model/adaptive_pointer_length_v023326/{pointer,hybrid,adaptive}.pt`.

Running three heads with token-by-token supervision can take longer than earlier diagnostic scripts.

## Interpretation

- If adaptive gate improves in-pool test but not unseen IDs, gating is still distribution-bound.
- If teacher-forced position correctness improves on long sentences while exact copy remains zero, autoregressive error accumulation and/or EOS may limit results.
- If long copy improves, repeat with a genuinely independent fixed holdout and more than one random seed before claiming robust length generalization.
- Three heads have different numbers of trainable parameters; this is a feasibility comparison, **not a parameter-matched causal ablation**.

This experiment does not change DSS, Semantic Memory, Semantic Bridge, or existing checkpoints; it does not establish semantic understanding.
