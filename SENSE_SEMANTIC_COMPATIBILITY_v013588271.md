# v0.13.58.82.71 — Sense / Semantic Memory Compatibility Diagnostic

This version inspects the 4 quality-gated v0.70 sense candidates against the existing **atomic proposition** store (read-only). The detector distinguishes:
- EXACT_VALUE_MATCH: normalized exact wording
- POSSIBLE_ELABORATION: one value text contains the other
- REVIEW_SENSE_OR_CONFLICT: same subject, different values (not necessarily contradictory)
- NO_MATCHING_SUBJECT: no matching atomic proposition
- BLOCKED_UNQUALIFIED: missing quality gate, subject or meaning

No semantic entailment or contradiction claims are made. The diagnostic does not yet scan all unified knowledge sources or the internalized model. No candidate is imported, approved, or learned.

PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.71-semantic-compatibility
    python -m unittest -v test_sense_semantic_compatibility_v013588271.py test_sense_definition_quality_v013588270.py test_sense_review_v013588269.py
    python sense_semantic_compatibility_v013588271.py --candidates results/sense_definition_quality_v013588270.json --propositions data/semantic_propositions_v1090.jsonl --output results/sense_compatibility_v013588271.json

Result: an offline compatibility matrix, no writes to Semantic Memory. The next phase can add read-only unified/typed/Truth State cross-checking before proposing a gated import.
