# v0.13.58.80 — Answer Reuse Verifier (fail-closed baseline)

This is a conservative **label-blind** verifier, not a trained classifier. It triages candidate pairs based on textual risk cues and ensures that a high relative ranking score cannot be treated as evidence of answer correctness.

All nonempty pairs currently return REVIEW, except missing fields which return REJECT; **ACCEPT is intentionally disabled** pending an independent verifier and calibration set. Tests cover risk cases and false-accept prevention. No runtime integration, /sleep or weights are changed.

Input CSV columns: `query_id,candidate_id,query,candidate_question,candidate_answer,score,answer_reusable`. The last field is used only in post-decision evaluation, never in `verify`. You may join the reviewed-pair file to ranking-score CSV using (query_id,candidate_id), but inspect source column names before constructing the input; don't fabricate missing scores or answers.

```powershell
git fetch origin
git switch v0.13.58.80-answer-reuse-verifier
python -m unittest -v test_answer_reuse_verifier_v0135880.py
python answer_reuse_verifier_v0135880.py --input data/verifier_pairs_v0135880.csv --output results/answer_reuse_verifier_v0135880.json
```

This version measures a zero-coverage, zero-false-accept baseline, not a usable auto-accept gate. Further work: add calibrated evidence/entailment verifier with independent dev/test splits and auditable accept decisions.
