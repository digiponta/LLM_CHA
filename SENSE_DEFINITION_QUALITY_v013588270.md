# LLM_CHA v0.13.58.82.70 — Sense Definition Quality Gate

This is an offline post-discovery quality gate. It does not change the model, chat.py, chat_gui.py, or Semantic Memory.

- Drop non-definition historical narratives, including the observed Big Bang theory historical acceptance sentence.
- Normalize leading Japanese punctuation in the extracted meaning.
- Require a definition-like predicate or supported nominal ending.
- Regenerate deterministic candidate IDs after normalization, and include an old-to-new migration table.
- Forbid automatic review transfer even if the ID is unchanged; every candidate remains pending manual review.
- Keep removed candidates in rejected diagnostics for audit.

This conservative rule set may reject valid but unusually written definitions; inspection remains required. All Wikipedia snapshots are truncated and external unverified.

Windows PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.70-sense-definition-quality
    python -m unittest -v test_sense_definition_quality_v013588270.py test_sense_review_v013588269.py test_sense_discovery_v013588268.py
    python sense_definition_quality_v013588270.py --source results/sense_discovery_v013588268_fixed.json --output results/sense_definition_quality_v013588270.json
    Get-Content results/sense_definition_quality_v013588270.json -Encoding UTF8

To inspect staging with the quality-controlled candidates (existing reviews with old IDs are never carried over):

    python review_sense_candidates_v013588269.py --report results/sense_definition_quality_v013588270.json --reviews data/sense_human_reviews_quality_v013588270.json --stage-output results/sense_approved_staging_quality_v013588270.json

Expected on user's five-record snapshot: four candidate definitions and one rejected historical narrative; never conflate that expectation with independently verified accuracy. No direct memory import or human approval is performed.
