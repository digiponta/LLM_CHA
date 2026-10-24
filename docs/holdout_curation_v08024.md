# LLM_CHA v0.8.0.24 — Holdout curation

The inventory tool is read-only and **does not** produce or validate evidence.

Run in PowerShell:

```powershell
git switch v0.8.0.24
python -m unittest -v test_inspect_curated_holdout_v08024.py
python inspect_curated_holdout_v08024.py data/curated_holdout.json
```

Curate at least five **independently sourced** `UNSEEN_FACT` records
with unique `id`, `question`, `reference_answer`, `source_url`,
`source_excerpt`, and `evaluation_kind: UNSEEN_FACT`.

Use the structure below only as a schema illustration, not as real evaluation data:

```json
{
  "independent_source_attested": false,
  "records": []
}
```

Mark `independent_source_attested: true` **only after** personally
confirming independent provenance, reference answers, and no known exposure.
The flag is an attestation, not proof. Do not fabricate sources or answers.
Do not use test fixtures as experimental evidence.

After inventory reads `READY_FOR_FORMAL_GATE`, run
`python prepare_holdout_v08023.py data/curated_holdout.json`
**without** `--write`. The formal gate also checks against the training
candidate store and may reject items despite the inventory result.

The code does not prove semantic independence or knowledge accuracy;
semantic overlap review and independent final evaluation remain future work.
