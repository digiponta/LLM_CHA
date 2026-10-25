# v0.9.7.37 — Emotion/Strategy Factor Ablation

v0.9.7.36 found conditioned SFT 5/30 heldout exact matches, compared to
2/30 for daily SFT, but swapping only the emotion label did not lower
exact match accuracy (5/30). The model often emitted the same
disappointment response. Some apparent improvement therefore may be
response frequency bias rather than learned semantic control.

This version evaluates four variants on the SAME 37 development examples,
using a frozen v0.9.7.35 conditioned checkpoint:

- `correct`: correct emotion, correct strategy;
- `emotion_only_swapped`: changed emotion, unchanged strategy;
- `strategy_only_swapped`: unchanged emotion, changed strategy;
- `both_swapped`: both changed.

Each prompt gets the same deterministic generation settings. The report
contains full text, exact reference matches (holdout), change counts,
unique response counts, and most frequent output. 37 * 4 = 148
generation calls. This is diagnostic ONLY: changes in output are not
proof of meaning, and intentionally contradictory tags are out-of-
distribution. The 30 holdouts have already been inspected in past
iterations and are NOT a blind independent final evaluation.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.37

python -m unittest -v `
  test_emotion_ablation_v09737.py `
  test_emotion_generation_v09736.py

python evaluate_emotion_ablation_v09737.py `
  --conditioned model/model-llm-cha-emotion-conditioned-v09735.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output results/emotion_ablation_v09737.json
```

Results are written to the specified path, which must not already
exist. No training, checkpoint mutation, Semantic Memory changes, or
chat routing changes occur.

## Interpretation
- A high top-response rate in the `correct` arm indicates collapse.
- A response-change count after swapping only emotion reveals
  sensitivity to emotion markers, not necessarily correct behavior.
- A response-change count after swapping only strategy isolates
  sensitivity to strategy markers.
- If the model still emits a disappointment response for positive or
  negated sadness after correct tags, promote neither the model nor
  the sampled generations.
- Next phase: inspect category-specific failures and create an
  independently authored final benchmark before retraining.
