# LLM_CHA v0.8.0.25 — Holdout leakage triage

Run on Windows:

```powershell
git fetch origin
git switch v0.8.0.25
git pull --ff-only origin v0.8.0.25
python -m unittest -v test_detect_holdout_leakage_v08025.py
python detect_holdout_leakage_v08025.py data/curated_holdout.json
```

The tool scans normalized text similarity across holdout question/reference answer
and training candidate subject/natural language/canonical text. It reports a
matching candidate ID and compared field pair but never writes to the dataset.

Statuses: `NOT_READY` (empty), `REVIEW_REQUIRED` (suspected overlap),
`NO_LEXICAL_FLAGS` (no detected lexical similarity),
`TRAINING_STORE_NOT_FOUND`, or input errors.

**Not a proof of semantic independence.** Paraphrases, entailment, corpus
pretraining exposure, and unobserved training sources may be missed. Do not
use this result as an independent benchmark certificate. A separate semantic
review and independent provenance audit remain required. The human-curated
holdout is currently empty; never fill it with fabricated facts or URLs.
