# LLM_CHA v0.2.33.31 — Explicit Copy Cursor & Pointer State

## Why this experiment

v0.2.33.30 confirmed that EOS separation and sampled-rollout-prefix training did not resolve length-12–18 copying: every tested head remained 0/40 long exact copies. The combined relative+monotonic position predictor held ~64% teacher-forced long-position accuracy, while many sequences terminated early.

## Four choices

1. `baseline`: frozen v0.2.33.28 Combined pointer, with original free decoding and same evaluation split generator.
2. `deterministic_cursor`: **hand-coded identity-copy algorithm** that reads input IDs in order and stops at the end. Serves as a ceiling/control, never a learned model result.
3. `learned`: train an action classifier from frozen Transformer state + previous predicted source index + number of emitted tokens: ADVANCE (+1), STAY (+0), SKIP (+2), STOP. The previous index is stateful during inference.
4. `cursor_pointer`: same learned action classifier plus a separately learned relative+monotonic Pointer as a one-position nearby alternative. Only a proposal within one index of current cursor is accepted.

Both learned arms receive clean-sequence action labels (ADVANCE for every copied ID, STOP when source consumed), teacher-forced prefixes and correct alignment as *training-only* supervision. At inference, there is no gold position or gold output and termination is predicted. The deterministic cursor uses the input source length as a task algorithm and should copy all groups perfectly, which says nothing about LLM generalization.

## Data / checkpoint selection

Same frozen v0.2.33.20 Transformer, same seed and synthetic data-generation protocol as recent pointer experiments. Training stages: 200 short, 200 length-diverse, and another 200 length-diverse examples. Validation comprises independent short and long data; choose best checkpoint based on their mean loss, not test performance. Evaluate each method on 40 examples apiece for Short, Long, Unseen IDs, Mixed IDs and Novel Extra.

Learned Cursor/Pointer module files are saved under `model/copy_cursor_v023331/` and report under `results/copy_cursor_v023331.json`. Base Transformer, DSS, Semantic Memory, and Bridge remain unchanged.

## Run

```powershell
git fetch origin
git switch v0.2.33.31
git pull origin v0.2.33.31
python -m py_compile copy_cursor_v023331.py
python -m unittest -v test_copy_cursor_v023331.py
python copy_cursor_v023331.py
```

Requires the existing v0.2.33.28 `model/relative_monotonic_pointer_v023328/combined.pt`.

## Reading results

If learned cursor improves Long, examine whether it simply reproduces the advance-until-end algorithm. If learned cursor fails but deterministic is perfect, that distinguishes the task's tractability from the head's inability to learn robust progression. The clean-source action labels make pure copy-task learning easy; do not infer general semantic alignment or natural-language abilities. Repeat across independent holdout data and multiple random seeds before promoting any module into stable runtime.
