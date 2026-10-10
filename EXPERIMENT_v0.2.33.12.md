# v0.2.33.12 — Core Architecture Integrity Audit

The user requested reconsideration of hidden internal implementation bugs after v0.2.33.10–11 repeatedly found improved teacher-forced next-token NLL without correct free copy.

## Static inspection findings

1. `model.py`: `LanguageModel.__init__` defaults `use_position_embedding=False`. Positional embeddings are only added in `forward_hidden` when enabled, and the checkpoint can override the constructor default through its `config`. **Do not assume the real checkpoint has disabled positions until inspected.**
2. Without explicit positions, the causal stack has no direct per-token absolute-position signal. **The causal mask and multiple layers can nonetheless yield indirect positional context; it is inaccurate to claim that such a model is exactly order invariant at arbitrary depth.** A 1-block no-position attention network with fixed final query is provably invariant to permutation of earlier tokens; a multi-block network generally is not.
3. `LanguageModel.generate` applies repetition penalty to `set(generated)` including the entire **input prompt**. This actively penalizes candidate copied tokens that appeared in the source. It may hurt copy fidelity; the previous penalty-1.0 ablation showed this is not the sole failure cause.
4. `generate` reindexes learned absolute positions as 0..context_length-1 for each truncated window. This is normal in a model using a fixed context window, but it alters the absolute frame as history slides.
5. `train_purpose_sft_v02324.encode_row` masks response-only targets at indices `len(prompt)-1` and beyond. This offset is correct for next-token prediction, matching earlier diagnostics.
6. `SelfAttention` uses QK scaling, a strict upper-triangle causal mask and softmax. No definitive forward-attention indexing bug is apparent on source inspection.
7. For output, the tokenizer uses NFKC, which may intentionally normalize distinctions (e.g. fullwidth/compatibility forms). Previous ordinary Japanese roundtrips passed; a full Unicode fidelity guarantee was not tested.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.12
git pull origin v0.2.33.12
python -m unittest -v test_audit_llm_core_v023312.py
python audit_llm_core_v023312.py
```

Result `results/core_architecture_audit_v023312.json` prints **actual** saved Base and Copy checkpoint positional configs and measures next-logit sensitivity to one token-order permutation. This is read-only, no retraining, no checkpoint overwrite.

## Decision

If the saved checkpoint shows `use_position_embedding=False`, consider a fresh, properly controlled positional-embedding training comparison against an equally trained no-position control. Adding a randomly initialized positional embedding to a trained checkpoint and comparing outputs immediately is not valid causal evidence. A more robust sequence copy task would require fresh, diverse synthetic training and a genuinely held-out benchmark.

Do not reconnect Semantic Bridge until model-side generation is verified. DSS and Semantic Memory are unchanged.
