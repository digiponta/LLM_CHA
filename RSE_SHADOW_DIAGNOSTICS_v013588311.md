# v0.13.58.83.11 — RSE shadow diagnostics

Input is the v0.13.58.83.10 **AI-provisional** 30-row shadow report: tp=0, fp=0, tn=7, fn=1, review_positive=5, review_negative=17. This is not a human-verified independent evaluation. Since nothing is accepted, precision is undefined and zero false accepts does not demonstrate safety.

This branch adds reason frequencies, reason-by-provisional-label counts, decision-by-label counts, and candidate IDs for investigating why 22/30 cases abstain.

Run locally:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.11-rse-shadow-diagnostics
python -m unittest -v test_rse_shadow_diagnostics_v013588311.py test_rse_shadow_v013588310.py
python diagnose_rse_shadow_v013588311.py
```

Read: `results/rse_shadow_diagnostics_v013588311.json`.

**Strict leakage boundary:** these test cases are diagnostic only. Do not change acceptance rules, lexical thresholds or model parameters based on this test result. Build a new development suite from dialogue-level TRAIN/VAL data, review examples separately, freeze proposed changes there, then evaluate once on untouched TEST. The output excludes raw conversation text. No changes to chat.py, model weights, RSE gate or automatic answer acceptance.
