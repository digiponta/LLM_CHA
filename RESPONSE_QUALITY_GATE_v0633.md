# LLM_CHA v0.6.33 — Reviewed Response Quality Gate

The v0.6.32 result passed keyword scoring, while producing:
- `こんばんは。お疲れ行きつけの患者役。`
- `ネコ領域に属する。`

These are now **FAIL** under a narrowly reviewed exact-answer gate. Existing
v0.6.32 metrics remain in `legacy_keyword_gate_pass`; the final `pass`
requires both the old keyword gate and `response_quality_v0633.pass`.

## Run

```powershell
git fetch origin
git switch --track origin/v0.6.33
python -m unittest -v test_response_quality_gate_v0633.py test_online_quality_v0632.py
python evaluate_online_quality_v0632.py `
  --before model/model-gpu-v1.6.2-online.pt `
  --after model/model-gpu-v0632-candidate.pt `
  --cases data/quality_cases_v0632.example.json `
  --output results/quality_gate_v0633.json
```

Expected for the supplied v0.6.32 answers: final gate FAIL (exit code 2);
`response_quality_v0633.quality_regressions` includes `greeting` and
`cat`, though new-knowledge acquisition passes.

This is NOT a general semantic evaluator. It fails closed unless a manually
reviewed full answer or fullmatch pattern is supplied. It also evaluates
raw generation only, not `chat.py` runtime, nor human conversational quality.
Customize `acceptable_answers` for each case. Do not deploy a candidate
solely because a small test set passes.
