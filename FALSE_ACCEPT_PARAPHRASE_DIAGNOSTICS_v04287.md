# LLM_CHA v0.4.28.7 — False ACCEPT & Paraphrase Diagnostics

Branch: `v0.4.0`. Read-only analysis of the 64-turn v0.4.28.6 quality triage report.

New files: `diagnose_false_accept_v04287.py`, `test_diagnose_false_accept_v04287.py`.

- Lists every non-abstaining `ACCEPT` as `ACCEPT_NEEDS_RELEVANCE_REVIEW`. **This is a review queue, NOT a proven false-ACCEPT count.**
- Flags missing/malformed accepted outputs separately from relevance.
- Lists abstentions for review; does not presume all abstentions are false.
- Compares fixed sets of question variants for GPU (B01/C01/C02/G01), LLM (B05/C03/C04), sleepiness (A04/C05/C06) and reading preferences (A09/C07/C08). Detects differences in answered vs abstained responses but does not assume exact semantic equivalence or establish accuracy.
- Includes blank human review fields for relevance, gate decision appropriateness, Japanese fluency, and persona consistency. Does not infer model quality using heuristic scores.
- Requires 64 distinct turn IDs, refuses overwrite and includes source SHA-256.

## Windows validation

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_diagnose_false_accept_v04287.py test_eval_quality_v04286.py test_capture_chat_benchmark_v04283.py test_prepare_chat_benchmark_v04282.py test_persona_response_shadow_v0421.py

python diagnose_false_accept_v04287.py `
  --input results/chat_quality_triage_v04286.json `
  --output results/false_accept_diagnostic_v04287.json
```

The diagnostic is development-only, not an independent benchmark. This update does not invoke the model/GPU, modify chat.py, adjust Truth Gate, learn from benchmark prompts or perform /sleep. Review raw answers manually before changing thresholds or training.
