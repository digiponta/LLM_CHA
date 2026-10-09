# LLM_CHA v0.2.31.3 — Semantic Intent Normalization

Status: GitHub implementation complete; Windows tests and evaluations pending.

## Design
Add a deterministic, auditable expression-normalization layer ahead of the existing v0.2.31.1 Dialogue Semantic State controller. The layer maps selected Japanese paraphrases to supported goal expressions. The original controller and v0.2.31.2 files are preserved unchanged.

v0.2.31.2's 24 single-turn and 5 multi-turn cases have already been inspected and are now a SEEN development set, not unseen holdout. A fresh prospective set of 12 single-turn and 2 multi-turn cases is authored separately. Neither corpus is a broad population sample. The system has no calibrated confidence and is not an LLM_SEM embedding system.

## Run in PowerShell

```powershell
git fetch origin
git switch v0.2.31.3
git pull origin v0.2.31.3
python -m unittest -v test_semantic_intent_v02313.py
python evaluate_semantic_intent_v02313.py
python semantic_intent_normalizer_v02313.py
```

Output: results/semantic_intent_normalization_v02313.json

## Interpretation
Compare baseline and normalized controllers on the seen development split and genuinely new evaluation split. Record remaining failures and unnecessary question rates. Intent normalization is a rules baseline, not learned semantic generalization; avoid calibrating to this fresh fixture before reserving a new final set. In subsequent work compare to Semantic Memory / LLM_SEM only once this benchmark has established a clear baseline.