# LLM_CHA v0.2.33.33 — Explicit Action State & Transition Learning

## Motivation

v0.2.33.32 learned task-conditioned ADVANCE/SKIP relatively well, but test exact matches were Identity **22/30**, Selective **24/30**, Repeat **0/30**, Prefix **9/30**, Mixed **0/30**. Representative Repeat/Mixed traces show prolonged STAY loops and poor transition back to ADVANCE/SKIP. These observations motivate adding **observable action-state features**, not forced task-specific rules.

## Four-arm ablation

All arms are independently initialized, have the same frozen v0.2.33.20 backbone, use the same data, learning rate, epoch count, and validation-selection policy.

| Arm | Extra features beyond task embedding, previous cursor position, output history length, source length |
| --- | --- |
| baseline | None |
| last_action | one-hot last *predicted/executed* action, including a start-state code |
| repeat_count | number of consecutive same-position selections and indicator of a repeat |
| transition_state | both last-action and repeat-count features |

The model **predicts** one of ADVANCE, STAY, SKIP and STOP. All actions, positions and repetitions come from the model's autonomous actions at inference time. The gold action sequence is used **only** in teacher-forced supervised training and evaluation. No decoding repair or fixed transition rule is introduced. The previous position and count are input-state observations, not the correct next action.

## Evaluation

The five task families are identical to v0.2.33.32: identity, selective, repeat, prefix and mixed. Each of train/validation/test uses disjoint source sequences; task-held-out token IDs and long-series test groups are evaluated without validation selection. Three epochs, best known-ID validation loss. Report full sequence exact match including EOS, correct EOS timing, first action error-position histogram, and fraction of cases with four or more consecutive STAY predictions.

Unlike the previous version, the same evaluation generator is used for all four arms. This is still a **single-seed synthetic test**, and arms have different parameter counts, so the experiment is not a strictly parameter-matched causal ablation.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.33
git pull origin v0.2.33.33
python -m py_compile cursor_action_state_v023333.py
python -m unittest -v test_cursor_action_state_v023333.py
python cursor_action_state_v023333.py
```

Saves `results/cursor_action_state_v023333.json` and four head checkpoints under `model/cursor_action_state_v023333/`. The script refuses to overwrite preexisting outputs.

## Interpretation

- Increased Repeat/Mixed exact accuracy together with reduced STAY-loop incidence supports the hypothesis that explicit action history helps.
- If all heads still fail STAY transitions, examine switching-action confusion under gold vs generated states and consider explicit finite-state **task programs** as a separate deterministic baseline.
- If performance only improves for Identity/Selective, action-state features are not sufficient for repetition and mixed-rule transfer.

No changes to previous checkpoints, DSS, Semantic Memory, Semantic Bridge or stable runtime.
