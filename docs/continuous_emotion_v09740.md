# LLM_CHA v0.9.7.40 — Continuous Affect Semantic State

Experimental rule: *「悲しくない」＝「嬉しい寄りのニュートラル」*.
Represent negation of a negative affect on a continuous bipolar axis
as **slightly positive neutral** (+0.25), not as fully positive JOY.
Similarly, negating JOY means slightly negative neutral (-0.25).
These are design constants, not psychological measurement.

The new `continuous_emotion_semantics_v09740.py` is **isolated from
chat.py**, model weights, and Semantic Memory. It accepts explicit
negation for SADNESS, JOY, ENJOYMENT, ANXIETY, ANGER and explicit positive/
negative cues. Contrasting explicit emotions take priority over weak
inferred neutrality. Independent multiple axes abstain rather than
compressing a multidimensional state into one scalar.

Examples:
- 悲しくないよ → SADNESS_JOY +0.25, POSITIVE_LEANING_NEUTRAL.
- 嬉しくない → SADNESS_JOY -0.25, NEGATIVE_LEANING_NEUTRAL.
- 不安ではない → ANXIETY_CALM +0.25.
- 悲しくない。むしろ嬉しい。 → explicit JOY +0.75.
- 嬉しいけれど悲しい → MIXED 0.0, BOTH explicitly present.

Negative/positive axis is an approximation: real emotion isn't
necessarily bipolar, and neutrality can coexist with other negative
feelings. Do not infer verified emotional states from an utterance.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.40
python -m unittest -v test_continuous_emotion_v09740.py test_emotion_quality_v09739.py
python evaluate_continuous_emotion_v09740.py --output results/continuous_emotion_v09740.json
```

No live route changes or training. Future evaluation should align
dataset categories with runtime categories, test negation scope,
double negation, sarcasm, contrast, and multiple axes, then compare
with v0.9.7.39 diagnostics before allowing any live deployment.
