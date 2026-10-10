# LLM_CHA v0.2.33.14 — Copy Learning Optimization Ablation

## Motivation

The v0.2.33.13 core verification passed: causal isolation, forward/generate parity, gradient propagation, checkpoint roundtrip and a single copy sentence reaching 100% teacher top-1 and exact free-generation match by step 25 at LR 2e-4 without replay. This does **not** establish unseen copying. Earlier v0.2.33.9 used LR 5e-6 with replay and failed all 12 copy probes. Their differences were confounded.

## Design

Use a four-arm 2 × 2 comparison, always initialized from `model/model-llm-cha-response-quality-v0221.pt`:

| Arm | Transformer LR | Head LR | Replay |
|---|---:|---:|---|
| low_replay | 5e-6 | 1e-6 | ON |
| high_replay | 2e-4 | 4e-5 | ON |
| low_no_replay | 5e-6 | 1e-6 | OFF |
| high_no_replay | 2e-4 | 4e-5 | OFF |

Common 20-item copy training corpus, identical update order, same number of copy updates, identical 5-item validation split and 8 novel held-out copy strings, same random seed, fixed epochs (default 8), shared weight decay 0.01 and greedy repetition penalty 1.0.

Replay-enabled arms spend extra compute on replay loss and this difference must be acknowledged; only first exploratory seed is run. Best validation-NLL checkpoint per arm is used for generation, separate from the last-step weights.

Reports include each arm's train/validation/replay NLL, exact copy counts for seen, unseen, novel combination and length cases, and actual greeting / acknowledgement / persona response outputs.

**Do not interpret loss improvement as copy transfer; no promotion or runtime switch.**

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.14
git pull origin v0.2.33.14
python -m unittest -v test_copy_optimization_ablation_v023314.py
python copy_optimization_ablation_v023314.py --epochs 8
```

Final summary: `results/copy_ablation_v023314/summary.json`.

Trained checkpoints: `model/copy_ablation_v023314/*.pt`. Reports are never silently overwritten. For rerun use new `--out-dir` and `--model-dir` directories.

## Interpretation

- High LR only helps training sentences: optimization was limiting, but generalized copying still absent.
- Replay ON preserves chat responses but compromises copy task: quantify interference.
- High LR + Replay preserves both: viable regime for scaling data, subject to independent evaluation.
- All arms fail even seen copying: test answer-prefix schedules, single-to-multi curriculum and held-out learning curves; do not assume an architecture defect based on the ablation alone.

DSS, Semantic Memory and semantic Bridge remain unchanged.
