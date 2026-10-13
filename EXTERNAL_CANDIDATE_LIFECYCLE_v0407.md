# LLM_CHA v0.4.7 — External Knowledge Candidate Lifecycle (Stage 1)

Provides an isolated JSON store for **v0.4.6 Japanese Wikipedia search results**. Records are keyed by SHA256 of [concept, URL]; duplicates are not re-added. Excerpt/description/title changes are detected via content fingerprint; the old content is retained (bounded history) and the record becomes `NEEDS_REREVIEW`. Identical re-imports preserve existing human review states. Every record remains `UNVERIFIED` and `eligible_for_training=false`. `APPROVED_FOR_REVIEW_ONLY` is a store marker, **not** Semantic Memory promotion or permission to train.

The input is checked for v0.4.6 schema, source URL domain, flags, size and duplicate IDs. An existing invalid store is refused rather than overwritten. Writes to the **designated isolated results JSON file only** are atomic; there is no database transaction, lock or concurrent-writer protection. Do not run concurrent imports into the same store. Search snippets are limited context and do not prove encyclopedic correctness or answer suitability.

No changes to `chat.py`, Persona Memory, Truth Gate, knowledge queues, model weights, existing candidate lifecycle or `/sleep`. No network access is performed here; import an already retrieved v0.4.6 report. No review-state editing CLI is exposed in this stage.

## PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_external_candidate_store_v0407.py test_wikipedia_candidate_v0406.py
python external_candidate_store_v0407.py --input results/wikipedia_candidate_v0406_novel.json --store results/external_candidate_store_v0407.json
# Repeat identical command; expected added=0, unchanged=5, updated=0.
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Share the output JSON summary. The observed v0.4.6 `小説` report has 5 candidate records, so initial import is expected to add 5 and the second unchanged import should add 0. This is a **prediction**, not yet a v0.4.7 measured outcome.

Next stages: explicit review workflow with traceable human approval and source/article suitability checks; only a separate opt-in path should later promote reviewed factual propositions, subject to Truth Gate and content-license requirements.
