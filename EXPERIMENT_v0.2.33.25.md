# v0.2.33.25 — Explicit Pointer/Copy Mechanism

## Motivation

v0.2.33.24 showed 0/20 long sequence exact-copy even after externally restricting candidates and forcing the correct EOS time, and 0/20 novel-token exact-copy with the Combined model. The next controlled question is whether a **learned source-position distribution** can improve copying without gold positions at inference.

## Architecture

The base Transformer checkpoint **v0.2.33.20** remains frozen. Two small trainable heads are learned independently with the same training/validation sequences and optimizer settings:

1. **Pointer-only:** use the frozen Transformer's final hidden states for the output-prefix query and source-token keys; train Q/K projections and an EOS position logit. Normalize attention scores over source positions plus EOS; scatter-add probabilities of repeated source IDs into the vocabulary distribution. Predict next token and EOS autoregressively.
2. **Pointer-Generator (Hybrid):** the same position/EOS pointer distribution blended with the frozen LM-head softmax through a learned sigmoid gate.

Teacher forcing during training provides the correct prior copied IDs and the matching source position as an **auxiliary supervised training target**. Neither matching source position nor true output length is supplied to the decoder at evaluation time.

This is a new trainable module, **not** an oracle that supplies the correct copy position. It is also not a demonstration of semantics.

## Data and evaluation

Common synthetic random ID sequences (disjoint at full sequence level):
- 200 train, 40 validation, 40 test; lengths 2–8 using IDs 8–71
- Long: 40 sequences length 12–18 from familiar IDs
- Unseen token IDs: 40 sequences using IDs 72–87
- Mixed: 40 sequences from known and unseen task IDs
- Extra novel: 40 sequences using IDs 88–103.

Validation loss chooses checkpoints, not any test/OOD result. Exact token-ID match includes EOS. The known base checkpoint was already trained on similar task IDs, which is a limitation. The new heads are initialized fresh.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.25
git pull origin v0.2.33.25
python -m py_compile pointer_copy_v023325.py
python -m unittest -v test_pointer_copy_v023325.py
python pointer_copy_v023325.py --epochs 4
```

Output: `model/pointer_copy_v023325/pointer.pt`, `model/pointer_copy_v023325/hybrid.pt`, `results/pointer_copy_v023325.json`. Outputs are not overwritten. This may take considerably longer than a no-training diagnostic because each copied token requires a frozen Transformer forward pass, independently for both heads.

## Interpretation

- Pointer-only success on genuinely held-out task token IDs indicates that *selecting an input position* transfers better than directly predicting an ID via the LM head.
- Pointer-only failure on long sequences suggests learning the matching input-position mapping and EOS remains difficult.
- Hybrid vs pointer-only indicates whether blending the pretrained language distribution helps or distracts from pure copying.
- Correct source position is a supervised training target; that does not imply algorithmic copy behavior emerges without position supervision.
- Compare with v0.2.33.20's test 36/80, long 0/40 and held-out IDs 0/40, but note dataset sizes and head training differ: this is a mechanism feasibility test rather than a perfectly controlled architecture ablation.

Do not merge these experimental heads into stable inference or Semantic Memory internalization without subsequent independent verification.
