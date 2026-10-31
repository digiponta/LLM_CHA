# v0.13.58.82.73 — Explicit Safe Semantic Memory Registration

The CLI distinguishes a missing knowledge store (SOURCE_NOT_FOUND) from an existing, valid, empty store (SOURCE_PRESENT, count=0). Unreadable data produces SOURCE_UNREADABLE. It supports **actual explicit registration** to the existing atomic proposition and unified memory stores. This is not an automatic promotion workflow.

## Requirements / boundaries
- Explicitly provide all five **actual existing** paths from your local Semantic Knowledge configuration (atomic, subject-index, typed-index, unified, truth), plus an existing provenance JSON file initialized to `[]`. The tool never creates a missing store.
- Candidate must pass definition quality gate, have complete provenance, no unresolved review flags, and match an explicit human APPROVE record (reviewer+reason and matching subject/meaning/evidence/source).
- Any matching subject in an existing store, or blocking truth state, blocks import pending merge review.
- Preview is read-only. `--commit` is required to write. The CLI will fail closed if any candidate in the batch is not eligible.
- Writes the actual atomic proposition store and updates the unified store with the project's existing `sync_subject_from_propositions` function; appends an external-unverified provenance entry. Runtime memory will use the same files if the configured paths match. Model weights and /sleep are unchanged.
- On catchable errors after write, previous files are restored. This is **not a full crash-safe multi-file transaction**: power loss between file replacements can leave partial writes. Back up your stores first, and do not run chat/sleep concurrently with registration. Additional index syncing may be required for other consumers: this version does not update subject/typed indexes.

## PowerShell

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.73-safe-semantic-registration
    python -m unittest -v test_safe_semantic_registration_v013588273.py test_sense_multilayer_compatibility_v013588272.py

Review existing path values in your local chat runtime settings; do NOT assume the path examples are real.
After checking a candidate's original evidence, record an individual human approval:

    python review_sense_candidates_v013588269.py --report results/sense_definition_quality_v013588270.json --reviews data/sense_human_reviews_quality_v013588270.json --candidate <EXACT_SENSE_ID> --decision APPROVE --reviewer local-reviewer --note "Confirmed source, meaning and scope"

Initialize a dedicated **new** provenance journal once (not an existing production knowledge file):

    New-Item -ItemType File -Path data/sense_registration_provenance_v013588273.json -Value "[]" 

Before running, set your actual knowledge store filenames. A missing file must be resolved by locating your configured runtime store—not by fabricating an empty replacement.

    $common = @(
      "--quality", "results/sense_definition_quality_v013588270.json",
      "--reviews", "data/sense_human_reviews_quality_v013588270.json",
      "--atomic", "<EXISTING_ATOMIC_PATH>",
      "--subject-index", "<EXISTING_SUBJECT_INDEX_PATH>",
      "--typed-index", "<EXISTING_TYPED_INDEX_PATH>",
      "--unified", "<EXISTING_UNIFIED_PATH>",
      "--truth", "<EXISTING_TRUTH_PATH>",
      "--provenance", "data/sense_registration_provenance_v013588273.json"
    )
    python safe_semantic_registration_v013588273.py @common
    # Only if every candidate is ready, backups are prepared, and there are no concurrent chat processes:
    python safe_semantic_registration_v013588273.py @common --commit

Because all four candidates remain unreviewed, the current data are **not eligible for registration yet**. Registration is enabled as a gated action, not performed on the user's behalf. For a single review, you may prepare a separate quality JSON containing only the reviewed candidate (do not alter any IDs/contents); inspect provenance and compatibility before registering.

## Important limitation
The tool only knows what's in the explicitly supplied files, not the model's learned weights or other storage backends. A reported absent subject is scoped to these validated stores, not the entire LLM.
