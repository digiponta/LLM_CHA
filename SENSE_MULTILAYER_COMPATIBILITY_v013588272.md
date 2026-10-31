# LLM_CHA v0.13.58.82.72 — Multi-Layer Semantic Compatibility

Read-only cross-layer inspection of four quality-gated sense candidates against atomic propositions, subject index, typed index, unified semantic memory and truth state. The output contains one compatibility classification per layer, rather than incorrectly concluding absent knowledge from atomic-only NO_MATCHING_SUBJECT. No auto-approval, auto-learning or memory import.

Note: the default unified and truth paths are example legacy store paths. Override them with the actual paths from your local chat.py configuration if different. A missing file produces an empty result, not proof of absent knowledge. The checkpoint and internalized learned weights are NOT examined in this version. A differing text is REVIEW_SENSE_OR_CONFLICT, not proven contradiction.

Windows PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.72-multilayer-compatibility
    python -m unittest -v test_sense_multilayer_compatibility_v013588272.py test_sense_semantic_compatibility_v013588271.py test_sense_definition_quality_v013588270.py
    python sense_multilayer_compatibility_v013588272.py --candidates results/sense_definition_quality_v013588270.json --output results/sense_multilayer_v013588272.json

Inspect data store paths and each layer's status before interpreting the report. Unknown/missing evidence and knowledge-layer heterogeneity are not validated facts.
