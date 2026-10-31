# v0.13.58.82.76 — Explicit Delegated Approval Gate

This isolated CLI allows exactly one current AI-reviewed sense candidate, **閃亜鉛鉱** (`sense-ab912703fcc269a1`), to be imported after an explicit user authorization token and a strict read-only readiness check. This is **not human approval**. It never changes v0.73's human review policy.

Requirements: all five stores must exist and be readable; original v0.70 candidate ID migration record must match; AI record must have exact matching subject, meaning, evidence and source URL, reviewer_type AI_DELEGATE, human_review_recorded false and decision RECOMMEND_APPROVE (not CAUTION or DEFER); no existing same subject in any store; no blocking truth record; existing distinct provenance audit file (JSON list). Only the frozen Wikipedia candidate is eligible. Missing/unknown data blocks import.

The explicit authorization flag is a runtime acknowledgement, not an authentication mechanism. `--commit` updates Atomic Proposition, Unified Memory and the provenance audit with `delegated_approved=true`, `human_approved=false`, `truth_verified=false`, `model_learned=false`. Other three candidates remain untouched. Subject and typed indexes are not synchronized in this version; external material remains unverified. This is NOT a crash-safe multi-file transaction; take backups and stop chat processes. A production system should additionally lock stores and use a durable journal.

Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.76-delegated-approval-gate
    python -m unittest -v test_delegated_semantic_import_v013588276.py test_delegated_sense_review_v013588275.py

Define existing paths:

    $delegated = @(
      "--quality", "results/sense_definition_quality_v013588270.json",
      "--ai-review", "results/sense_ai_delegated_review_v013588275.json",
      "--atomic", "data/semantic_propositions_v1090.jsonl",
      "--subject-index", "data/subject_keyed_propositions_v1090.jsonl",
      "--typed-index", "data/typed_subject_propositions_v10100.jsonl",
      "--unified", "data/unified_semantic_memory_v1090.jsonl",
      "--truth", "data/truth_state_v10103.jsonl",
      "--provenance", "data/sense_registration_provenance_v013588273.json",
      "--authorization", "I_DELEGATE_AI_REVIEW_FOR_SPHALERITE_V013588276"
    )
    python delegated_semantic_import_v013588276.py @delegated
    Get-Content results/sense_delegated_import_v013588276.json -Encoding UTF8

Only after checking the report, snapshot backups, and absence of concurrent processes:

    python delegated_semantic_import_v013588276.py @delegated --commit

Any failed check must be resolved before commit. A missing provenance file must not be confused with a missing semantic knowledge store. Verification of physical truth of claims by independent sources is not supplied; no automatic approval of CAUTION cases. This release implements bounded user-delegated registration capability, not a blanket automatic knowledge injection process.
