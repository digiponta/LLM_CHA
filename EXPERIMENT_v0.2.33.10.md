# v0.2.33.10 — Token-Level Copy Diagnostics

The v0.2.33.9 copy experiment yielded **0/4 memorized and 0/8 unseen literal exact-copy responses**, despite improved training NLL. The next diagnostic must establish whether failure occurs in tokenization, target alignment, token prediction or inference. This experiment **does not train** or modify DSS, Semantic Memory, Bridge or checkpoint assets.

## Scope

For three trained sentences and six unseen / novel-combination / long cases, compare the frozen original v0.2.21 checkpoint and copy-trained v0.2.33.9 checkpoint.

- Tokenizer encode/decode round-trip of prompt and target.
- Response-only target alignment from the actual v0.2.32.4 SFT `encode_row` implementation.
- Teacher-forced token NLL, per-token top-1 hit and target rank, including first response token.
- Free generation at temperature 0 both **without** repetition penalty (1.0) and with the historical runtime penalty (1.05).
- Exact copied-string match and EOS indicator.
- Detailed first 15 output token predictions in JSON.

Teacher forcing is not free decoding; using a gold suffix may mask error accumulation. Further causal attention probing may be required, but **do not infer attention failure** from generation output alone.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.10
git pull origin v0.2.33.10
python -m unittest -v test_token_copy_diagnostics_v023310.py
python token_copy_diagnostics_v023310.py
```

Saved report: `results/token_copy_diagnostics_v023310.json`.

## Next decision

- Roundtrip fails: investigate tokenizer normalization or decode.
- Alignment fails: investigate response-only masking or EOS shifted labels.
- Teacher first-token rank poor on trained texts: optimize response-initiation data, model capacity or training procedure.
- Teacher rank good but free generation poor: investigate sequence-level exposure bias, stop tokens and sampling/repetition penalties.
- Good first token but later target predictions weak: investigate long-horizon imitation and token-level error propagation.

This is a small deterministic diagnostic, not a semantic comprehension benchmark. Manual review is still necessary.
