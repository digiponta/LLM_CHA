# v0.13.58.82.55 Question-Aware Evidence Selection

Experimental **offline-only** evidence answer selection. Questions are classified into `definition`, `time`, `cause`, `mechanism`, `composition`, or `unknown`. The selector ranks complete original sentences from the saved source excerpt with lexical signals, then submits the selected sentence to the existing strict `evidence_gate`. No unsupported paraphrases or independent truth claims are introduced. If an attribute or source sentence is absent, the system abstains.

IMPORTANT: Attribute regexes are heuristics, not semantic entailment. A mention of `によって` alone does **not** prove that the evidence actually answers a causal question; audit such matches. The `EXTRACT_ACCEPTED` status means the copied sentence passes the substring gate; it does not mean the answer is correct, complete, or question-relevant. The source is EXTERNAL_UNVERIFIED. The GUI, original negative teacher signals, and production models are unchanged.

## Windows validation

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.55-question-aware-evidence
python -m unittest -v test_question_aware_evidence_v013588255.py test_evidence_decoding_v013588254.py
python evaluate_question_aware_v013588255.py `
  --evidence-json results/evidence_snapshot_v013588249.json `
  --output results/question_aware_evidence_v013588255.json
Get-Content results/question_aware_evidence_v013588255.json -Encoding UTF8
```

The default questions include the definition, age/timing, cause of expansion, and composition. Compare which source sentence was chosen and whether a question received an abstention. With a fixed snapshot, repeated runs are reproducible.

Next: independent annotated relevance/entailment holdout across distinct sources and negative controls, then integration into the GUI only after quality/retention tests.
