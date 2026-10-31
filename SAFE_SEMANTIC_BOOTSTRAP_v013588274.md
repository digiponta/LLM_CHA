# v0.13.58.82.74 — Safe Store Bootstrap

Purpose: keep the existing Unified Semantic Memory intact while making the four missing on-disk stores explicitly present. **Does not infer their contents from Unified data, does not approve candidates and does not register any knowledge.** Zero-record stores are not proof that a model lacks knowledge.

The bootstrap uses the read-only `store_status` loaders from v0.73 to distinguish SOURCE_NOT_FOUND, SOURCE_PRESENT (including count=0) and SOURCE_UNREADABLE. A missing or invalid Unified store blocks execution. Paths must not overlap. Bootstrap reads existing Unified bytes, validates them and backs them up. Explicit `--commit` creates only the four missing store files, with exclusive creation (no overwrite), and checks that Unified bytes were preserved. Existing non-Unified stores are left as is. A previously existing backup path blocks commit.

PowerShell, run with Chat closed and stores backed up:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.74-safe-store-bootstrap
    python -m unittest -v test_safe_semantic_bootstrap_v013588274.py test_safe_semantic_registration_v013588273.py
    $storeArgs = @(
      "--atomic", "data/semantic_propositions_v1090.jsonl",
      "--subject-index", "data/subject_keyed_propositions_v1090.jsonl",
      "--typed-index", "data/typed_subject_propositions_v10100.jsonl",
      "--unified", "data/unified_semantic_memory_v1090.jsonl",
      "--truth", "data/truth_state_v10103.jsonl"
    )
    python safe_semantic_bootstrap_v013588274.py @storeArgs
    Get-Content results/semantic_bootstrap_v013588274.json -Encoding UTF8

If and only if the preview confirms the actual runtime paths and the expected missing stores, and no other process has open write access:

    python safe_semantic_bootstrap_v013588274.py @storeArgs --commit
    python safe_semantic_bootstrap_v013588274.py @storeArgs

The four missing stores should become SOURCE_PRESENT with count=0. The existing unified file must retain its original SHA256; the backup path is in the report. Then re-run the v0.73 readiness diagnostic with the same verified paths and the real human review file. The review count currently is zero, so import will be blocked until explicit reviews exist. Do not add `--commit` to v0.73 before all conditions are checked.

Limitations: the sequence of file creations is not a crash-safe multi-file transaction; an unexpected power loss may leave some empty files created. It does not synchronize the derived Subject/Typed indexes or search alternate live stores. It prevents accidental overwrites and restores files created in the current run after catchable exceptions.
