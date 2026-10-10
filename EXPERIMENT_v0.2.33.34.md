# LLM_CHA v0.2.33.34 — Transition State Robustness & Action Composition

## Motivation

v0.2.33.33 (one seed) improved Repeat and Mixed compared with the baseline task-conditioned Cursor:
- Standard Test: Baseline 62/150; Last Action **92/150**; Repeat Count 69/150; Transition State **90/150**.
- Long: Baseline 35/200; Last Action 49/200; Transition State **65/200**.
- Long Repeat: 0/40 (Baseline), 19/40 (Last Action), 27/40 (Transition State).
- Novel Extra: 55/200 (Baseline), 76/200 (Last Action), 93/200 (Transition State).

Before further changing the architecture, establish stability across independent random seeds and inspect **which action transition first fails**.

## This version

Freeze the common v0.2.33.20 LanguageModel and **retrain independently for each seed**:
- Baseline: previous Cursor without explicit previous-action state.
- Last Action: add one-hot previous action.
- Transition State: previous action and repeat counter.

By default train 3 seeds **42, 43, 44**, 3 epochs each, train/validation/test split per seed, identical per-seed datasets across arms. Report group and task exact-match counts for short, long, unseen task IDs, mixed IDs and additional novel IDs. Compute cross-seed mean/min/max/std exact-match proportions.

For each autonomous generation trace, find the first Action mismatch. The confusion matrix counts aligned gold-prefix actions plus the first divergent action **only**: after divergence, correct gold alignment is not available. Report first-error-position histograms and >=4 STAY-action loops. This avoids conflating long mismatched rollouts with meaningful gold state targets.

### Crucial limitation: "unseen action composition"

The existing architecture takes **one of five known task names**, not a program of arbitrary action instructions. It is therefore invalid to claim a valid test of an unseen composition solely by fabricating a new action sequence at evaluation. This script records several novel example scripts in `heldout_action_scripts_reference_only` **without model scores**. Proper unseen-rule generalization requires a *script-conditioned* decoder or a withheld task rule with an explicit condition representation. This is proposed for the next implementation after robustness diagnosis.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.34
git pull origin v0.2.33.34
python -m py_compile cursor_transition_robustness_v023334.py
python -m unittest -v test_cursor_transition_robustness_v023334.py
python cursor_transition_robustness_v023334.py
```

Results: `results/cursor_transition_robustness_v023334.json`. Script refuses overwrite. This re-trains 9 heads (3 arms x 3 seeds) so runtime will be significantly longer than v0.2.33.33. To first run a limited smoke test, use `--seeds 42 --train-count 12 --val-count 6 --test-count 6 --epochs 1 --out results/cursor_transition_robustness_smoke_v023334.json`. That smoke test is not the full research result.

### Scientific cautions

The arms differ in head parameter count, and the pretrained Transformer remains the same across seeds; only head initialization and generated data split vary. Repeated examples reuse the same five pre-specified tasks; success would establish **sequence and token-ID holdout stability**, not novel-rule generalization or semantic understanding. Never merge experiment heads into Semantic Memory, Bridge or stable runtime without independent validation.
