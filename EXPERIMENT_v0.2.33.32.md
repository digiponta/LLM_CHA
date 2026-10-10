# LLM_CHA v0.2.33.32 — Cursor Generalization & Action Learning

## Goal

v0.2.33.31: Learned Cursor achieved **37/40 short, 24/40 long, 13/40 unseen IDs, 32/40 mixed IDs, 16/40 novel extra** on sequential identity copying. That result does not demonstrate that the head knows how to selectively choose, repeat, or stop at arbitrary source positions.

This version tests a single **task-conditioned learned action head** on five rules. The task name is given to the model; the correct actions and output are not available at inference:

| Task | Target positions for source length n |
|---|---|
| identity | 0,1,2,…,n-1 |
| selective | 0,2,4,… |
| repeat | 0,0,1,1,…,n-1,n-1 |
| prefix | 0,…,ceil(n/2)-1 |
| mixed | 0,0,2,2,4,4,… |

Four action labels: ADVANCE (+1), STAY (+0), SKIP (+2), STOP. The training compiler generates the gold action sequence, which supervises the new action head; the head predicts the actions during free decoding. A fixed task embedding disambiguates the requested operation. Backbone Transformer parameters remain frozen. **This is task-conditioned synthetic action generalization, not natural-language instruction understanding**.

## Data / evaluation

Default train 120 independent known-ID source sequences (600 task examples), validation 30 source sequences (150 task examples), test 30 source sequences (150 task examples). Other groups each use 40 source sequences (200 task examples):
- long: source length 13–18
- unseen: task-held-out IDs 72–87
- mixed IDs: known + task-held-out
- novel extra: IDs 88–103.

Full-sequence ID overlap is prevented among train/validation/test and all default generated groups use different seeds; explicit task labels may recur. No task family is held out from training, so do not claim unseen action-rule generalization.

The model trains all five task families and selects an epoch based on separate known-ID validation sequences. Metrics: exact token-ID match including EOS, prefix-aligned action accuracy, EOS timing accuracy, and per-case action traces.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.32
git pull origin v0.2.33.32
python -m py_compile cursor_generalization_v023332.py
python -m unittest -v test_cursor_generalization_v023332.py
python cursor_generalization_v023332.py
```

Outputs: `results/cursor_generalization_v023332.json`, `model/cursor_generalization_v023332.pt`. Refuses overwrite; uses three epochs and a frozen base checkpoint. Five task families per source require more time than a single identity-copy training run.

## Limitations and next decision

The rules themselves are simple and known during training; the task type is explicitly supplied at inference, and features include input length and generated history length. Strong results would show generalization to new **sequences and token IDs within these rules**, not arbitrary extraction plans or semantic understanding. If learned head excels only on identity/prefix, add balanced action losses and separately measure SKIP/STAY confusion. If it succeeds across all five, evaluate unseen compositions and natural-language-to-action grounding in a subsequent version.

Do not integrate this experimental module into DSS, Semantic Memory, or Stable Runtime without independent evaluation.
