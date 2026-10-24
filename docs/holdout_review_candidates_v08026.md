# Holdout review candidates v0.8.0.26

This is a **source-backed proposal**, not a verified independent evaluation set.
The five reference answers were drafted from public primary-source pages.
They have **not** been compared to local training candidates, base-model
pretraining, existing prompts, or earlier exposure histories.

- `independent_source_attested` is **false** by design.
- Review claims against the cited pages; check timestamps, question scope, and provenance.
- Review the local training candidate store and remove duplicates/semantic overlap.
- After review, copy only genuinely unseen, independently sourced records into
  `data/curated_holdout.json`, leaving `independent_source_attested`
  false until a human has actually confirmed it.
- `UNSEEN_FACT` indicates intended evaluation category, **not** a proven state.
- Do not use these candidates as a final holdout until the independence audit.

Run:

```powershell
python detect_holdout_leakage_v08025.py data/holdout_review_candidates_v08026.json
python inspect_curated_holdout_v08024.py data/holdout_review_candidates_v08026.json
python prepare_holdout_v08023.py data/holdout_review_candidates_v08026.json
```

The latter two should not return READY while attestation remains false.
Do not use `--write` during review.
