# v0.13.58.82.44 — Negative teacher signals only

Following user request, **/good and automatic positive-answer learning have been removed**:
- GUI `/good` does not approve anything, train, or forward to CLI.
- GUI `/repair ...` commands no longer approve or teach; legacy repair queue file remains on disk for compatibility.
- CLI `/good` is disabled.
- Each Evidence Gate `REJECT_*` candidate is automatically recorded to `data/negative_teacher_signals_v013588244.jsonl`. Duplicate same question/candidate/gate signals are suppressed by SHA-256.
- Signal fields include question topic, rejected text, gate, source context URL, `signal: NEGATIVE`, `weight: -1`, `training_status: NOT_TRAINED`. The -1 is a **label**, not a gradient step.
- The `online_train.py` negative-weight default is now 0.0. Neither model weights nor checkoints are changed by a rejection; old /train manual functionality remains available for other explicitly provided training pairs, but it is not triggered by GUI rejection.

## Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.44-negative-only
python -m unittest -v test_negative_only_v013588244.py
python chat_gui.py
```

Generate an Evidence-Aware reply that is rejected. Confirm `[Negative Teacher Signal] RECORDED` or `DUPLICATE` in Diagnostics. `/good` should report disabled. No automatic training is invoked.

Existing trusted learning rows and already learned checkpoints are not rolled back by this change. A future isolated trainer can consume the negative signal queue with an independently controlled objective and evaluation; this release only records the signals.
