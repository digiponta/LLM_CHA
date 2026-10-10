# LLM_CHA v0.2.33.30 — Decoupled EOS & Rollout Alignment

## Background

v0.2.33.29 diagnosed Long (40 series) for the v0.2.33.28 Combined head:
- teacher-forced pointer position accuracy: 64.1%
- free-decoding pointer position accuracy: 46.9%
- EOS: early 26, correct 2, late 12
- autonomous complete copies: 0/40.

The observations motivate testing separate EOS scoring and training with model-generated history.

## Four experimental arms

All arms have the same **frozen** v0.2.33.20 Transformer and use an otherwise comparable Combined relative + monotonic pointer:

| Arm | EOS | Training history |
| --- | --- | --- |
| combined | Existing EOS scoring | Gold prefixes |
| decoupled | Separate trainable stopping MLP | Gold prefixes |
| rollout | Existing EOS scoring | Gold prefixes + model-sampled prefixes |
| decoupled_rollout | Separate stopping MLP | Gold prefixes + model-sampled prefixes |

The separate stop score includes a progress ratio: number of output tokens / input length; both quantities are available at inference. No gold pointer position or externally forced EOS is supplied at generation time.

**Caution:** A distinct EOS head may learn the sequential length identity task without learning a general stopping mechanism. The experimental output cannot prove open-domain EOS control. The rollout arm samples model-produced prefixes (not synthetic gold prefixes), then supervises the next position using the sampled prefix length. This is an **off-policy recovery surrogate**, not true on-policy optimization or a proof that a skipped token can be recovered. Training losses/parameter counts are not exactly matched across all arms.

## Shared schedule and evaluation

For every arm, use 200 short known-ID sequences at Stage 1; 200 sequences length 2–18 at Stage 2; repeat long-range training at Stage 3. Select checkpoint by equal-weight short/long **validation** loss, never by test data. Each arm evaluates the same five groups with 40 series per group: short-known-ID test; long-known-ID test; task-held-out-ID; mixed-ID; extra novel-ID.

Metrics: autonomous full ID-copy accuracy including EOS, teacher-forced position accuracy, teacher-forced EOS accuracy, and autonomous EOS early/correct/late/missing classes.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.30
git pull origin v0.2.33.30
python -m py_compile decoupled_eos_rollout_v023330.py
python -m unittest -v test_decoupled_eos_rollout_v023330.py
python decoupled_eos_rollout_v023330.py
```

Outputs: `results/decoupled_eos_rollout_v023330.json` and four experimental head checkpoints inside `model/decoupled_eos_rollout_v023330/`. Existing files/checkpoints are not overwritten.

Training runs four arms; the rollout conditions additionally sample model prefixes and can be slow.

## How to decide the next experiment

- EOS-only gain with unchanged pointer accuracy: keep stopping as a separate research module.
- Rollout-only gain in autonomous long copying: independently repeat across seeds and held-outs before making generalization claims.
- Both improve: investigate whether they interact or duplicate advantages.
- Neither improves: return to position alignment, possibly a deterministic task-specific copy baseline and a learned position-offset target.

No merge into DSS, Semantic Memory, Semantic Bridge or Stable Runtime is made by this experiment.
