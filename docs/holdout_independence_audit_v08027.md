# v0.8.0.27 — Human provenance and overlap audit

Run locally (PowerShell):

```powershell
git fetch origin
git switch v0.8.0.27
git pull --ff-only origin v0.8.0.27
python -m unittest -v test_audit_holdout_independence_v08027.py
python audit_holdout_independence_v08027.py data/holdout_review_candidates_v08026.json
```

The tool checks required evidence metadata, surfaces lexical/topic overlap
with local training candidates, and requests manual review. For each record,
review the primary source, actual answer, and previous training exposure.

Optional review file:
```json
{"reviews":[{"id":"review-mars-moons-001","source_checked":true,
"answer_checked":true,"training_nonoverlap_checked":true,
"overlap_manually_resolved":false}]}
```

Only use true for a field **after personally completing that check**.
No review file is shipped with positive attestations.

Important limits: topic overlap is a heuristic, not a semantic model. This
tool does not fetch citations, verify truth, rule out base-model pretraining
exposure, or approve a final holdout. `MANUAL_REVIEW_RECORDED` records
human declarations; it is not proof of statistical independence.
Never auto-set `independent_source_attested` or run `--write` based only on
this audit.
