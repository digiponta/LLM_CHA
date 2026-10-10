# LLM_CHA v0.2.33.29 — Pointer Error Propagation & Alignment

## Background

v0.2.33.28: baseline long teacher-forced source-position accuracy 46.0%, relative 60.3%, monotonic 51.8%, combined 64.1%. Long complete token-ID copy including EOS was **0/40 in all four models**. More accurate teacher-forced alignment is not yet translating into robust autonomous long copying.

## Frozen diagnostic

Read the four v0.2.33.28 saved heads (no training, no checkpoint modifications), and recreate the same evaluation groups using the same seed and data generator.

For each group and head, compare:

- **Free-decoding pointer positions:** source positions selected while using the model's OWN previously generated tokens (and previous predicted pointer location if monotonic). No gold history or positions are injected.
- **Teacher-forced pointer positions:** predictions with the gold token history, for diagnosis only.
- First **token** error, first **source-position** error, absolute source-position drift, and autonomous token-ID exact copy.
- EOS classification: early, correct, late, or missing.
- Complete per-case traces (input IDs, output IDs, predicted positions) for detailed subsequent analysis.

The gold position is used to **score** free-decoding outputs but never to choose them. The trace uses a decoding budget of max(32, source length + 5). Once EOS is generated decoding stops. Note that predicted pointer position can differ from the canonical source position yet generate the correct token if the same ID appears repeatedly. Early EOS means subsequent positions are unobserved.

## Commands

```powershell
git fetch origin
git switch v0.2.33.29
git pull origin v0.2.33.29
python -m py_compile pointer_error_propagation_v023329.py
python -m unittest -v test_pointer_error_propagation_v023329.py
python pointer_error_propagation_v023329.py
```

Prerequisite: four `v0.2.33.28` head checkpoints are present in `model/relative_monotonic_pointer_v023328/`.

Output: `results/pointer_error_propagation_v023329.json` (refuses overwrite). Results are descriptive only: single random seed and synthetic copying task. No DSS, Semantic Memory, Bridge or previous checkpoints are modified.

## Next decision

- If the free-vs-teacher position gap is large immediately after the first error, focus on robust rollout / on-policy training.
- If teacher position remains weak at late steps, focus on position-alignment architecture or length-balanced training.
- If positions remain accurate but EOS early/late dominates, investigate explicit EOS training and calibrated stopping separately.
