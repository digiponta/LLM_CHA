# v0.13.58.82.77 — AI Individual Review + Human yes/no Batch Approval

This release adds an explicit, bounded workflow:
1. AI reviews individual candidates, keeping AI reviewer attribution.
2. The preparation stage selects **only** unambiguous RECOMMEND_APPROVE candidates that are quality-gated, provenance-bound, not already registered, and not present in any store.
3. The complete eligible set and the SHA-256 hashes of all five stores plus audit journal form a frozen batch hash.
4. The human sees the complete selected and excluded items and types exactly `yes` or `no`. This decision is recorded separately from AI review.
5. The separate commit action re-checks quality, reviews and store bytes against the manifest and approval, then appends atomic propositions, rebuilds subject and typed indexes, updates unified memory and appends a provenance audit entry.

A batch `no` does not write knowledge. Conditional AI recommendations and DEFER are excluded. The prior successfully registered 閃亜鉛鉱 candidate is also excluded because it already exists. **For current four known candidates this means there may be zero eligible entries.** The command must then correctly refuse batch approval; do not force it. To test end-to-end with real knowledge, prepare new qualified, unregistered candidate(s).

Limitations: explicit input typed at the console is the local human approval indication (not identity authentication); source trust remains EXTERNAL_UNVERIFIED. There is no automatic Truth State validation of external correctness. Atomic + derived indexes + unified + audit are updated with rollback on ordinary exceptions, but this is not power-loss-safe or concurrent-writer-safe; stop chat/sleep and back up the stores. A future release should implement a write-ahead journal and OS-level lock.

## Windows

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.77-batch-human-approval
    python -m unittest -v test_batch_semantic_approval_v013588277.py test_delegated_semantic_import_v013588276.py

    $batch = @(
      "--quality", "results/sense_definition_quality_v013588270.json",
      "--ai-review", "results/sense_ai_delegated_review_v013588275.json",
      "--atomic", "data/semantic_propositions_v1090.jsonl",
      "--subject-index", "data/subject_keyed_propositions_v1090.jsonl",
      "--typed-index", "data/typed_subject_propositions_v10100.jsonl",
      "--unified", "data/unified_semantic_memory_v1090.jsonl",
      "--truth", "data/truth_state_v10103.jsonl",
      "--provenance", "data/sense_registration_provenance_v013588273.json"
    )
    python batch_semantic_approval_v013588277.py prepare @batch
    Get-Content results/sense_batch_manifest_v013588277.json -Encoding UTF8

When eligible_count is positive, inspect the manifest and approve interactively:

    python batch_semantic_approval_v013588277.py approve @batch
    # Prompt: Approve exactly these eligible entries? [yes/no]:
    # Only type yes if you actually authorize the displayed batch.

After closing Chat, making reliable backups, and checking the recorded approval:

    python batch_semantic_approval_v013588277.py commit @batch

`prepare` never changes production knowledge. `approve` writes only the separate approval artifact. `commit` writes production knowledge only if every check passes.
