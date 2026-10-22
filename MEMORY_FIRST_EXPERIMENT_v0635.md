# v0.6.35 — Semantic Memory First (isolated comparison)

The v0.6.34 GPU sweep had 0/8 candidates passing full answer quality.
This experiment tests a **reviewed exact-QA memory overlay** against the
baseline answers from `quality_gate_v0632.json`. It makes NO modifications to
production Semantic Memory, `chat.py`, the model weights, or the original report.
It is an isolated retrieval simulation, **not** a verified production runtime.

## Windows
```powershell
git fetch origin
git switch --track origin/v0.6.35
python -m unittest -v test_memory_first_v0635.py test_response_quality_gate_v0633.py
python evaluate_memory_first_v0635.py `
  --baseline-report results/quality_gate_v0632.json `
  --cases data/quality_cases_v0632.example.json `
  --overlay data/semantic_memory_first_v0635.example.jsonl `
  --output results/semantic_memory_first_v0635.json
```

The exact test question is explicitly approved in the example JSONL and
is derived from the earlier controlled learning pair. Outputs include
per-question provenance and route information. Unapproved rows are ignored;
conflicting approved rows error out.

Expected: on the supplied v0.6.32 baseline report, the controlled memory
overlay can answer the new question while leaving existing baseline answers
unchanged. This is **not evidence that chat.py already implements this path**.

Future: integrate an approved-knowledge route into the real chat runtime;
evaluate paraphrases, conflict/truth gates, multi-turn prompts and the full
protected QA suite before any production decision. Keep `/sleep` opt-in.
