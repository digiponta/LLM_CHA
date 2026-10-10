# LLM_CHA v0.2.33.22 — Length & Vocabulary Generalization

## Background

v0.2.33.21 diagnosed token-ID copying: length 2 achieved 12/12, length 9–18 achieved 0/120, and held-out token IDs achieved 0/40. For long sequences, 78/120 were classified as early EOS, with other content and late-EOS failures.

## Experiment

Create four newly trained experimental checkpoints starting **independently from the same frozen v0.2.33.16 language checkpoint**, `model/model-llm-cha-general-copy-v023316.pt`. v0.2.33.20 is a historical comparison, *not* the common initializer.

| Arm | Training sequence lengths | Training data-token IDs |
|---|---|---|
| baseline | 2–8 | 64 (IDs 8–71) |
| length | 2–18 | 64 (IDs 8–71) |
| vocabulary | 2–8 | 80 (IDs 8–87) |
| combined | 2–18 | 80 (IDs 8–87) |

All arms: 400 train examples, 6 epochs, common checkpoint, optimizer config, training-order seed and 2–8/known-ID validation distribution. Training data is separately sampled from the relevant distribution; sequences don't overlap test/validation data. Parameter-update counts match across arms, but longer examples cost more tokens/compute.

Evaluation after best validation-NLL selection uses shared, held-out:
- `short`: 80 known-ID sequences, length 2–8.
- `long`: 40 known-ID sequences, length 12–18.
- `expanded`: 40 sequences drawn from 80 IDs.
- `novel_only`: 40 sequences drawn exclusively from IDs 88–103, unseen as task source/target in **all** arms.
- `novel_mix`: 40 sequences from both known/added/new ID pools.
- `validation`: 80 known-ID sequences.
- `training_probe`: 40 per-arm seen sequences.

Outputs report exact token-ID sequence match **including EOS**, by-group accuracy and per-length counts.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.22
git pull origin v0.2.33.22
python -m unittest -v test_token_copy_factorial_v023322.py
python token_copy_factorial_v023322.py --epochs 6
```

Outputs: `results/token_copy_factorial_v023322/summary.json`, per-arm JSONs, and four checkpoints in `model/token_copy_factorial_v023322/`. Existing artifacts are not overwritten; choose fresh `--out-dir` and `--model-dir` paths for reruns.

## Caveats

This is a single-seed controlled synthetic ablation. New ID range 88–103 was excluded from task training but may have appeared during base-model pretraining. The common validation distribution favors known-ID short sequences, so the selected checkpoint may not maximize length transfer. Do **not** use the held-out tests for model selection. The purpose is to isolate length and vocabulary exposure, not claim semantic or arbitrary-language copying. DSS, Semantic Memory and Semantic Bridge remain untouched.
