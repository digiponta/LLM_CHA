# v0.8.0.28 — Numeric-only false-positive reduction

This version keeps all provenance and human approval checks from v0.8.0.27.
Only topic matches consisting entirely of numbers or a short list of generic
tokens are suppressed, unless lexical similarity exceeds 0.80.

Run on Windows PowerShell:
```powershell
git fetch origin
git switch v0.8.0.28
git pull --ff-only origin v0.8.0.28
python -m unittest -v test_audit_holdout_independence_v08028.py
python audit_holdout_independence_v08028.py data/holdout_review_candidates_v08026.json
```

Expected: the numeric-only "2" overlap in the Mars moons candidate should
be suppressed; SI "基本単位" should remain under review. Exact output depends
on local candidate data. Human provenance review remains required.
No source URLs are fetched or verified; no model weights or holdout data change.
This is **not** LLM_SEM embedding similarity, and does not establish independence.
