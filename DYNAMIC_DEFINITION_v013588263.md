# v0.13.58.82.63 Dynamic Subject Binding & Definition Extraction

Offline-only guarded experimental addition. New module identifies a subject from the matched article title and aliases, accepts explicit lead-style definitions with source-exact Evidence Gate, rejects cross-topic source mismatch and obvious historical descriptions, preserves the v0.62 extraction routes for time/composition/cause and CPU. This is limited pattern extraction, not a model-based generalized subject recognizer, scientific verification, or human-approved holdout.

Files:
- evidence_dynamic_definition_v013588263.py
- evaluate_dynamic_definition_v013588263.py
- test_dynamic_definition_v013588263.py

Windows PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.63-dynamic-subject-definition
    python -m unittest -v test_dynamic_definition_v013588263.py test_evidence_alias_binding_v013588262.py test_evidence_cause_binding_v013588259.py
    python evaluate_dynamic_definition_v013588263.py --real-data data/wiki_evidence_review_v013588260.json --synthetic-data data/independent_binding_eval_v013588258.json --output results/dynamic_definition_v013588263.json
    Get-Content results/dynamic_definition_v013588263.json -Encoding UTF8

Review individual sentences. The eight Wikipedia source excerpts are truncated at 900 characters, remain external unverified and pending human review. Any additional extracted answers are NOT established correct. The original 12 synthetic cases are development data, not independent holdout. Do not change the baseline dataset to inflate accuracy. No production GUI, checkpoints or automatic learning behavior changed.
