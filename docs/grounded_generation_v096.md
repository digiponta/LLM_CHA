# v0.9.6 Grounded Semantic Response Generation — experimental A/B stage

This version **does not** replace the proven `chat.py` answer path or
perform actual LLM-conditioned decoding yet. It adds a reproducible harness
to evaluate LLM-generated candidate answers against v0.9.5 baselines.

The candidate source must be explicitly recorded by the researcher. The
heuristic gate checks answer length, topic mention, rough lexical alignment,
unsupported certainty, and disclosure of unverified corpus evidence.
Passing the gate is **not** scientific verification, entailment, or proof of
generation quality. The holdout data must remain independent.

Example `data/grounded_ab_example_v096.jsonl` contains one candidate that
passes the heuristic and one that is rejected.

```powershell
git fetch origin
git switch --track origin/v0.9.6
python -m unittest -v test_grounded_generation_gate_v096.py test_context_aware_response_v095.py test_question_aware_evidence_v0943.py test_corpus_role_classifier_v0942.py test_explicit_topic_corpus_v0941.py test_response_quality_v094.py test_topic_suggestion_followup_v093.py test_topic_suggestion_v092.py test_corpus_answer_plan_v091.py
python compare_grounded_generation_v096.py data/grounded_ab_example_v096.jsonl results/grounded_ab_v096.json
```

Before claiming a real LLM-vs-baseline improvement: integrate an actual
model generation adapter with logged model/checkpoint, capture candidate
outputs on disjoint held-out questions, and compare factual consistency,
persona consistency, topic continuity, and quality with manual auditing.
No model weights, corpus evidence, approvals, or Semantic Memory change.
