# LLM_CHA v0.1.0 — Development Baseline

Status: **development branch**, not a stable release.

## Starting point

- Parent: `main`, migrated from LLM_TRY v10.17.0.
- Preserve the existing semantic proposition, subject-keyed memory, typed/conditional retrieval, approval gates and `/sleep` pipeline.
- Do not retrain, overwrite checkpoints, or change `chat.py` as part of the first milestone.

## Milestone 1: character profile foundation

Files:
- `character_profile_v010.py`: immutable character metadata, UTF-8 JSON persistence and validation.
- `test_character_profile_v010.py`: standard-library-only profile regression.

Run on Windows / PowerShell:

```powershell
git fetch origin
git switch v0.1.0
git pull --ff-only origin v0.1.0
python -m unittest -v test_character_profile_v010.py
```

No GPU or model checkpoint is required for this test.

## Next milestones (not implemented yet)

1. Integrate opt-in profile selection into `chat.py` without altering default behavior.
2. Separate character style, conversational context, and factual Semantic Memory.
3. Route factual output through the existing truth/unknown/approval gates.
4. Add character consistency and no-profile compatibility regressions.
5. Test `/sleep` with approved facts only; persona/style metadata must not automatically become a fact.
6. Run legacy stable regression suites before proposing merge to `main`.

## Acceptance criteria

- Existing no-profile conversations remain unchanged.
- Profile save/load is deterministic and Japanese text round-trips.
- Character styling cannot independently mark facts as known or override gate decisions.
- `/sleep` promotion requires the existing verification/approval pathway.
- Existing LLM_TRY-derived regression suites pass before release.

This branch has NOT yet passed the full legacy runtime regression or GPU-based evaluation.
