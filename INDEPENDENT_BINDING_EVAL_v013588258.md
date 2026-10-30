# LLM_CHA v0.13.58.82.58 — Synthetic Adversarial Binding Evaluation

Adds 12 manually authored positive and adversarial cases covering Universe, Big Bang, Sphalerite, event-time anaphora, definition/history confusion, and a different unsupported subject.

IMPORTANT: These synthetic fixtures are NOT an independent statistical holdout and do NOT provide a generalization estimate. They are diagnostic cases. They are not real Wikipedia excerpts.

Metrics:
- false_accept_rate = accepted unanswerable negative cases / negative cases.
- coverage = all accepted cases / all cases.
- selective_accuracy = correctly accepted cases / accepted cases.
- answerable_recall = correct accepted positive cases / positive cases.
- accepted_error_rate counts both accepted negatives and incorrectly matched positive-answer values.
- false_negative counts answerable positive cases for which the system abstains.

One positive cause example intentionally exposes the currently conservative refusal to answer causal questions. This should count as lost recall, not a success.

Windows PowerShell:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.58-independent-binding-eval
    python -m unittest -v test_independent_binding_v013588258.py test_evidence_definition_anaphora_v013588257.py
    python evaluate_independent_binding_v013588258.py --data data/independent_binding_eval_v013588258.json --output results/independent_binding_eval_v013588258.json
    Get-Content results/independent_binding_eval_v013588258.json -Encoding UTF8

Review false accepts and abstentions. For publication-quality claims, independently collect and attest separate real-world sources, human-written answer annotations and leakage control. No production weights, GUI, or learning policy changed.
