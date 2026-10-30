# LLM_CHA v0.13.58.82.61 — Alias and real-source review diagnostics

Adds a read-only diagnostic path for the 8 Wikipedia records collected in v0.60. The prior report had 8 collected, 0 failed, but all records pending review and all excerpts truncated to 900 chars.

Files:
- evidence_alias_normalization_v013588261.py: minimal aliases (スファレライト/閃亜鉛鉱; 中央処理装置/CPU) and explicit composition surfaces (硫化亜鉛→ZnS, H2O).
- evaluate_evidence_alias_review_v013588261.py: subject matches, evidence composition candidates, excerpt hash consistency, truncation and review-gate reasons.
- test_evidence_alias_review_v013588261.py: six tests including non-invention and no-auto-approval.

A normalized formula is a mapping of an expression present in the text, not independent verification. These diagnostics do not automatically change the v0.59 binder, the GUI, or human review fields. The eight public articles are a diagnostic dataset, not an attested independent holdout.

PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.61-alias-review
    python -m unittest -v test_evidence_alias_review_v013588261.py test_real_evidence_holdout_v013588260.py
    python evaluate_evidence_alias_review_v013588261.py --data data/wiki_evidence_review_v013588260.json --output results/evidence_alias_review_v013588261.json
    Get-Content results/evidence_alias_review_v013588261.json -Encoding UTF8

Expect REAL_EVIDENCE_DIAGNOSTIC_ONLY, records=8, holdout_approved=false and review gate reasons remaining. Review or replace all truncated evidence and document any independence checks separately; never auto-approve human attestations.
