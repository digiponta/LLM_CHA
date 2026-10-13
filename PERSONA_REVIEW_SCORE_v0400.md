# LLM_CHA v0.4.0 — Human-Reviewed Persona Role Scoring

Development branch: `v0.4.0`; preserved baseline: `v0.3.7.8-verified`. No changes to `main`.

The v0.3.7.8 audit reported **four** corpus candidates and **8/8 source-lookup probes**, but **0 human judgments**. The probe hit rate is *not* semantic extraction precision.

This stage introduces `persona_review_score_v0400.py`. Its inputs are the original corpus and the editable CSV from `persona_review_v0378.py`. It verifies the candidate ID, source text, roles and coordinates against the **current** raw corpus and rejects duplicated IDs, missing rows, invalid verdicts, or altered source fields. Edit only `verdict` and `note` in the CSV.

Supported verdicts: `CORRECT`, `AMBIGUOUS`, `INCORRECT`, and `UNREVIEWED`. It reports `precision_reviewed` only over adjudicated rows; the complete set's precision is **null while any row remains UNREVIEWED**. Reviewed `CORRECT` candidates are listed in a report for future consideration only; the runtime does not load or promote them. Truth Gate, `chat.py`, model weights and original corpus are unchanged.

## Commands

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v test_persona_review_score_v0400.py test_persona_review_v0378.py
python persona_review_score_v0400.py --corpus data/data-nagato.txt --csv results/persona_review_v0378.csv --report results/persona_review_scored_v0400.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

A score of `null` with all four cases unreviewed is expected and correct. Human review is required for a meaningful precision estimate.
