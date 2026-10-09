# LLM_CHA v0.2.31.6 — Structured Purpose Generalization Evaluation

Evaluation-only branch from v0.2.31.5: the parser is frozen. A 22-utterance prospective diagnostic set covers individual purposes, multi-purpose cases, sequential goals, preference/negation and ambiguous/unknown utterances.

Metrics: topic accuracy, ordered purpose-list accuracy, purpose-set equality, relation accuracy, polarity accuracy, dialogue action accuracy, all-field accuracy, and overcommit rate on six purpose-absent examples. Compare vector-only nearest-exemplar purpose classification to v0.2.31.5 structured parsing. Small hand-written evaluation; results are diagnostic, not proof of open-domain generalization.

## Windows commands
```powershell
git fetch origin
git switch v0.2.31.6
git pull origin v0.2.31.6
python -m unittest -v test_structured_purpose_v02316.py
python evaluate_structured_purpose_v02316.py
```

Output: results/structured_purpose_v02316.json

Do not alter the estimator or test labels after seeing results and then describe the same set as untouched holdout. Use observed errors for the next development version and reserve another fresh evaluation split.