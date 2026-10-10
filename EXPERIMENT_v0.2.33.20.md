# v0.2.33.20 — Algorithmic Copy Generalization

## Goal

The previous curriculum reached 144/144 exact copies within expanded synthetic templates but **0/29 on newly authored OOD examples**. This experiment intentionally separates the question **"Can the decoder copy unfamiliar token sequences?"** from Japanese lexical/grammar generation.

## Setup

Use the existing v0.2.33.16 checkpoint as initialization; the experiment **does not alter that checkpoint**. Learn a strictly token-level task with sequences encoded as:

```text
BOS MARKER [source token IDs] MARKER [same token IDs] EOS
```

Loss is masked on both the source and the second marker. Only the copied token IDs and EOS are predicted, exactly matching the autoregressive generation prefix `BOS MARKER source MARKER`. The marker (ID 7) and data IDs are disjoint from special tokens, checked at runtime.

**Training set:** 400 randomly constructed token-ID sequences of length 2–8 from a pool of 64 token IDs. **Validation:** 80 separate examples from the same pool; the best checkpoint is selected **only by validation NLL**.

After checkpoint selection, evaluate:
- 400 training sequences;
- 80 in-pool held-out sequences, independent from validation (the test group);
- 40 sequences longer than training (length 12–18);
- 40 sequences using 16 held-out token IDs;
- 40 sequences mixing in-pool and held-out IDs.

The model is scored with **exact token-ID match including EOS**, and initial correct prefix length. These probes are unseen as complete sequences; newly held-out IDs may still have appeared during *base-model pretraining*, so this is not a claim of totally unseen embeddings.

NFKC has no effect on this token-ID scoring: investigate Unicode fidelity separately using non-normalizing encoding only if lossless Unicode copying is an explicit goal.

## Commands (PowerShell)

```powershell
git fetch origin
git switch v0.2.33.20
git pull origin v0.2.33.20
python -m unittest -v test_algorithmic_copy_generalization_v023320.py
python algorithmic_copy_generalization_v023320.py --epochs 6
```

Outputs are experimental and overwrite-protected:
- `model/model-llm-cha-algorithmic-copy-v023320.pt`
- `results/algorithmic_copy_v023320.json`

## Interpretation

If in-pool held-out sequences generalize but held-out token IDs fail, learning is vocabulary-bound. If long sequences fail, length extrapolation remains a problem. If training fits but in-pool test fails, the model may memorize individual token series rather than the source-to-target copy operation.

The test is intentionally unlike natural language. Passing it would establish only algorithmic ID-sequence copying under this source marker protocol, not grounding or semantic understanding. DSS, Semantic Memory and Semantic Bridge remain unchanged.
