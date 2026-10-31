# LLM_CHA v0.13.58.82.68 — Sense Discovery (Review Candidates)

The experiment discovers definition candidates from source-exact article sentences. Each candidate has subject, meaning, evidence sentence, deterministic ID, source URL and unverified status. Potential duplicates and conflicts are flagged against a supplied list of known candidates. All candidates remain `PENDING_HUMAN_REVIEW`, `POSSIBLE_DUPLICATE`, or `POSSIBLE_CONFLICT`; nothing is automatically approved, promoted to Semantic Memory, or learned into weights.

This is a **read-only offline evaluation module**. It is deliberately not connected to the runtime's answer selection; v0.67's source-backed routing stays unchanged.

On Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.68-sense-discovery
    python -m unittest -v test_sense_discovery_v013588268.py test_generalized_sense_v013588267.py test_universe_sense_notice_v013588266.py
    python evaluate_sense_discovery_v013588268.py --data data/wiki_evidence_review_v013588260.json --output results/sense_discovery_v013588268.json

The source snapshots are truncated and have not undergone independent review. Extraction candidates are hypotheses, not validated meanings. Duplicate/conflict checks are preliminary lexical checks, not semantic entailment tests. Runtime CLI and GUI were intentionally not modified in this step.
