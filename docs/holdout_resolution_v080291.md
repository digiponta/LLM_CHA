# v0.8.0.29.1 — Resolve reviewed overlap flags safely

The v0.8.0.28 inspector retains `POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP`
even when `overlap_manually_resolved` is explicitly true. This wrapper
distinguishes manually resolved flags from open warnings, without erasing
the original `overlap_candidates` or promoting Holdout.

```powershell
git fetch origin
git switch v0.8.0.29.1
git pull --ff-only origin v0.8.0.29.1
python -m unittest -v test_audit_holdout_independence_v080291.py
python audit_holdout_independence_v080291.py data/holdout_review_candidates_v08026.json --review data/holdout_review_local_store_checked_20261024.json
```

When the review declares three checks true plus an explicitly resolved overlap,
the record has `overlap_review_resolution: MANUALLY_RESOLVED` and
`MANUAL_REVIEW_RECORDED` may be returned. **This is not final Holdout
approval**, nor evidence of independence from base-model pretraining or other
corpora. `formal_holdout_approved` stays false, and `--write` is not used.
