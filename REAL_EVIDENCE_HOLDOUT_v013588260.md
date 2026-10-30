# LLM_CHA v0.13.58.82.60 — Real-source evaluation preparation

Added Python files: collect_real_evidence_v013588260.py, evaluate_real_evidence_v013588260.py, test_real_evidence_holdout_v013588260.py.

The collector retrieves Japanese Wikipedia plaintext through the MediaWiki API, records the first 900 chars, article title and URL, page ID, UTC timestamp, SHA256, and whether the extract is truncated. Errors are reported rather than fabricated.

The evaluator refuses to score without at least five cases and explicitly human-reviewed source/question independence, answerability, required answer text for positive cases, and reviewer notes. New records begin as PENDING_HUMAN_REVIEW and EXTERNAL_UNVERIFIED. Initial evaluation should return NOT_READY. The provided seeds are NOT a statistically independent holdout. The review fields do not establish true independence without outside evidence.

Review workflow:
1. Verify article text against the saved excerpt; note truncation and relevance.
2. Independently label answerable; for answerable questions supply a required_substring from the actual answer.
3. Verify that sources and questions have not been used for training, tuning or previous benchmark-driven selection, and only then attest source_independent=true.
4. Record reviewer_note and status APPROVED_BY_HUMAN. Never mark unexamined records as reviewed.
5. Evaluate only after the gate reports ready; do not lower it to obtain metrics.

Windows PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.60-real-evidence-holdout
    python -m unittest -v test_real_evidence_holdout_v013588260.py test_evidence_cause_binding_v013588259.py
    python collect_real_evidence_v013588260.py --output data/wiki_evidence_review_v013588260.json
    Get-Content data/wiki_evidence_review_v013588260.json -Encoding UTF8
    python evaluate_real_evidence_v013588260.py --data data/wiki_evidence_review_v013588260.json --output results/real_evidence_holdout_v013588260.json
    Get-Content results/real_evidence_holdout_v013588260.json -Encoding UTF8

No production weights or GUI route are modified.
