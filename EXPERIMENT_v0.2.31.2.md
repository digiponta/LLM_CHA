# LLM_CHA v0.2.31.2 — Purpose Generalization & Confidence Calibration

Status: diagnostic suite committed; Windows tests and dataset evaluation pending.

## Aim
Measure how well v0.2.31.1's deterministic purpose controller handles held-out paraphrases, ambiguous goals, negatives, and multi-turn corrections **before** changing the recognizer. Do not conflate simple keyword-rule confidence scores with probabilities of correctness.

## Protocol
- 24 fixed independent single-turn phrases: 4 learning, 4 development, 4 troubleshooting, 4 casual, 4 ambiguous, 4 negation.
- Five multi-turn sequences covering confirmation yes/no, goal changes, and unknown-to-known transition.
- Report exact purpose/action success, category breakdown, sequence pass rate and empirical accuracy grouped by the controller's heuristic confidence values.
- Reliability bins exclude ambiguous purpose-null cases; this is an exploratory calibration diagnostic, not statistical calibration or an independent population benchmark.
- A purposeful failure is useful evidence of missing coverage. Do not tune on these fixtures and then call them unseen holdouts.

## Windows

```powershell
git fetch origin
git switch v0.2.31.2
git pull origin v0.2.31.2
python -m unittest -v test_purpose_generalization_v02312.py
python prepare_purpose_generalization_v02312.py
python evaluate_purpose_generalization_v02312.py
```

Expected output: data/purpose_generalization_v02312/{single_turn,multi_turn}.jsonl and results/purpose_generalization_v02312.json.

## Next
After the diagnostic, use a separate development set to improve robust intent normalization, confirmation triggers, negation, and question selection. Reserve a fresh untouched final set to estimate generalization. Future integration with LLM_SEM is a separate experiment.