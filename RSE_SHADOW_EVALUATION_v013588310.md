# RSE shadow evaluation v0.13.58.83.10

The v0.13.58.83.09 review contains 30 AI-provisional annotations (6 reusable, 24 not reusable), not independently confirmed human labels. This branch re-loads the test-split source locally, joins cases by ID, and runs the existing RSE candidate gate **only in shadow mode**.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.10-rse-shadow-evaluation
python -m unittest -v test_rse_shadow_v013588310.py test_rse_human_review_v013588309.py
python evaluate_rse_shadow_v013588310.py
```

The review must have nonempty `new_query`, all four Boolean labels, and IDs exactly matching the sampled source. Exact repeat of the source question is rejected to discourage trivial evaluation. This is only a weak independence safeguard; paraphrase semantic independence and original human annotator verification are not guaranteed.

The evaluator uses the stricter conjunction of intent_match, slot_match, answer_suitable, and NOT persona_transfer_risk as a reusable label, which can differ from v0.13.58.83.09's less restrictive summary counts. No model weights, training data, chat.py runtime, or auto-approval path are modified.

Metrics: accept candidate precision/recall, false acceptance rate among negative examples, candidate coverage, abstention rate. Abstentions remain separate from REJECT and are not counted as automatic acceptance. No raw source question/answer is stored in `results/rse_shadow_evaluation_v013588310.json`.

Labels are AI-provisional; results **cannot** be cited as human-verified holdout performance. Future: human verification on fresh question paraphrases and a disjoint development split for any further gate tuning.
