# LLM_CHA v0.2.33.15 — Checkpoint Selection & Copy Fidelity

v0.2.33.14 compared high/low LR with/without replay, but performed copy evaluation only on **best validation-NLL** checkpoints. High-LR models reached near-zero train NLL at epoch 8, while best validation loss occurred at epoch 1. Therefore those final weights were never tested for copy fidelity.

## Experiment

Run **one identical high-LR no-replay training trajectory** (base v0221; 20 train, 5 validation, 8 unseen/novel/length tests), and snapshot all 8 epochs. Select three checkpoints *from the same trajectory*:

1. **Best validation NLL** (teacher-forced validation loss).
2. **Final epoch** (last trained weights).
3. **Best seen copy** (maximum exact-string free-generation copy successes on 4 training examples; ties by validation NLL).

Evaluate each on 4 seen + 8 held-out (3 unseen, 3 novel-combination, 2 long) cases. Record exact text and exact token match including EOS. All results are exploratory; using seen copies to select a checkpoint does not constitute an independent validation scheme.

The default training condition deliberately matches the high-LR/no-replay arm of v0.2.33.14: LR 2e-4, head LR 4e-5, 8 epochs, weight decay .01, seed 42, repetition penalty 1.0 at evaluation.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.15
git pull origin v0.2.33.15
python -m unittest -v test_checkpoint_selection_copy_v023315.py
python checkpoint_selection_copy_v023315.py --epochs 8
```

Result: `results/checkpoint_selection_v023315/summary.json`.

Saved **experimental-only** checkpoints: `model/checkpoint_selection_v023315/{best_validation,final_epoch,best_seen_copy}.pt`.

The script will refuse to overwrite output directories. For a new run, specify both `--result-dir` and `--model-dir` anew. Existing base checkpoints and DSS, Semantic Memory and Bridge are untouched.

## Interpretation

- Final/seen-selected model copies trained strings, while validation-selected model does not: checkpoint selection masked memorization in v0.2.33.14.
- All three fail: high-LR multi-sentence copy learning has a further limitation, despite small teacher-forced loss.
- Held-out copy succeeds: investigate whether performance is robust to seed and out-of-distribution sources before promotion.
