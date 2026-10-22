# v0.6.34 Forgetting-Aware Replay Sweep

Tests candidate training under 2 learning rates x 2 epoch settings x 2 stability
replay weights. Each run creates independent checkpoint, state JSON and quality
report under `results/quality_sweep_v0634/`. Production state and checkpoints
are not updated. The baseline model is checked for byte-for-byte stability.

## PowerShell
```powershell
git fetch origin
git switch --track origin/v0.6.34
python -m unittest -v test_forgetting_replay_sweep_v0634.py test_response_quality_gate_v0633.py
python sweep_forgetting_replay_v0634.py
```

Required inputs: an existing baseline checkpoint, tokenizer,
`data/quality_training_v0632.jsonl`, `data/stability_replay_v104.jsonl`,
and `data/quality_cases_v0632.example.json`. Candidate artifacts can be
large. Override `--learning-rates`, `--epochs`, `--stability-weights` to
limit GPU runs.

## Interpretation
The strict v0.6.33 gate is retained. A fail is a meaningful diagnostic, not
a Python failure. No candidate is auto-promoted.

The tiny QA set is NOT enough to claim general retention; this is a first
controlled sweep of the previously observed greeting/cat degradation.
Evaluate expanded paraphrases and the full chat runtime before adoption.
