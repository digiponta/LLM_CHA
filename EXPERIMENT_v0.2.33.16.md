# LLM_CHA v0.2.33.16 — Generalized Copy Learning

## Purpose

v0.2.33.15 established that a high-LR, no-replay model copies **4/4 seen samples** from epoch 2, although validation-NLL model selection chose an early checkpoint with 0/4. It did not copy any of eight held-out unrelated sentences. This experiment tests **generalization to novel combinations of familiar Japanese words** rather than merely fitting the original 20 training strings.

## Dataset

A deterministic grammar combines eight color forms, eight objects, eight locations and four verbs, yielding 2,048 distinct sentences. Seeded disjoint splits: **480 train, 80 validation, 80 test**. No exact sentence overlaps occur. Every lexical item and template pattern is available during training; the test therefore measures new **combinations**, not unseen concepts or arbitrary natural-language copying.

Training response is the exact source sentence. Tokenization follows the same response-only objective and prompt as v0.2.33.9.

## Evaluation protocol

- Same base checkpoint, fixed seed, configurable epochs; default LR 5e-5 (head 1e-5), no replay in this pilot.
- Select only by **validation teacher-forced NLL**; hold test aside until after training and selection.
- Evaluate best-selected checkpoint on 40 sampled training examples, 80 validation and 80 held-out test sentences, with greedy generation and repetition penalty 1.0.
- Report full generated text and strict exact-match rate.
- No inference engine, DSS, Semantic Memory or Bridge changes.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.16
git pull origin v0.2.33.16
python -m unittest -v test_generalized_copy_learning_v023316.py
python generalized_copy_learning_v023316.py --epochs 8
```

Outputs:
- `model/model-llm-cha-general-copy-v023316.pt`
- `results/generalized_copy_v023316.json`

Outputs refuse overwrite; use new `--output` and `--report` filenames for reruns. Model is **experimental only**.

## Interpretation

Test exact-copy success is evidence of compositional copying in this constrained grammar, **not evidence of unconstrained copying or semantic comprehension**. Failure despite strong training fit would motivate analyzing input conditioning and output-token dependency. Repeated runs and different grammar splits are required before claims of robust generalization.
