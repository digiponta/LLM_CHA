# LLM_CHA v0.13.58.82.59 — Explicit Cause Relation Binding

Adds a narrow offline cause binder. Instead of treating generic "によって" as proof of causation, it accepts only a sentence explicitly identifying "宇宙の膨張の原因は、Xによる..." with an extractable X. Other relation types delegate to the unchanged v0.57 binder. All adopted sentences must still pass the source substring Evidence Gate. Source provenance is EXTERNAL_UNVERIFIED, and this checks **surface causal attribution**, not scientific truth or formal entailment.

The 12-case synthetic diagnostic set includes one answerable causal case, alongside negative controls for effect statements, another subject, unrelated dates, historical definitions and unsupported queries. Target on this authored set: 5 accepted, 5 correct, no false accepts or false abstentions. These are **targets, not verified observations**. No independent factual holdout or GUI integration is claimed.

## Windows PowerShell

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.59-cause-binding
    python -m unittest -v test_evidence_cause_binding_v013588259.py test_independent_binding_v013588258.py
    python evaluate_cause_binding_v013588259.py --data data/independent_binding_eval_v013588258.json --output results/cause_binding_eval_v013588259.json
    Get-Content results/cause_binding_eval_v013588259.json -Encoding UTF8

Review accepted cases and false accepts as well as aggregate metrics. Future work: genuinely independent annotated documents, richer subject/event normalization, source reliability and ambiguity checks; only then consider GUI integration. Model weights, /good behavior and the production checkpoint remain unchanged.
