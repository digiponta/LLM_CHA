# LLM_CHA v0.6.32 — Paired checkpoint quality and forgetting

This is a READ-ONLY quality evaluation: no training occurs and no checkpoint or
learning-state contents are changed. Run only with an actual candidate checkpoint
you have retained from a separate training run.

## Tests
```powershell
git fetch origin
git switch --track origin/v0.6.32
python -m unittest -v test_online_quality_v0632.py test_gpu_online_integrity_v0631.py
```

## Evaluate actual baseline vs candidate
```powershell
python evaluate_online_quality_v0632.py `
 --before model/model-gpu-v1.6.2-online.pt `
 --after model/model-gpu-v0632-candidate.pt `
 --cases data/quality_cases_v0632.example.json `
 --output results/quality_gate_v0632.json
```

The `--after` checkpoint above is an example path and must exist; this
evaluation script does NOT create it. v0.6.31's temporary probe model is deleted
when the integration test ends and cannot serve as this candidate.

Replace the sample "new_training_example" QA entry with a question/answer
actually used in your candidate's training, and add more protected tests before
drawing conclusions.

## Scoring and limitations
- Generation is greedy (temperature 0), direct language-model-only.
- `expected_any` uses string matching: it is a narrow regression metric,
  not semantic truth validation.
- Gate fails closed without a baseline-correct protected case and without
  a new-knowledge case.
- For stricter reporting, add multiple paraphrases and human-reviewed reference
  answers; later evaluate the entire chat runtime to capture retrieval and
  persona routing.
