# v0.9.7.39 — Semantic Response Quality (Exploratory)

The v0.9.7.38 four-arm experiment found reduced top-response collapse,
but exact matches cannot measure semantic appropriateness. This branch
adds a transparent **lexical rubric** and exports 148 annotated response
rows for **independent manual review**.

Rubric verdicts:
- PASS: explicit, category-compatible cues;
- FAIL: explicit contradiction or malformed text;
- REVIEW: insufficient evidence or ambiguous natural language.

Scores are heuristic **diagnostics**, not proof of semantic understanding,
naturalness, subjective empathy, or factual correctness. A low automatic
FAIL count may mean a high REVIEW count. Do not use the automated
measure as a single leaderboard without checking manual reviews.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.39
python -m unittest -v test_emotion_quality_v09739.py
python evaluate_emotion_quality_v09739.py `
  --input results/emotion_factorial_v09738.json `
  --output results/emotion_quality_v09739.json `
  --review-csv results/emotion_quality_review_v09739.csv
```

The CSV has `manual_verdict` and `manual_notes` columns for blinded
review. For rigorous scoring, remove the arm labels before adjudication,
randomize response rows, require two raters and resolve disagreements.
The inputs are previously inspected development cases, *not* an unseen
test set. No model training, chat routing, or Semantic Memory writes
are performed.

Next, evaluate a frozen rubric on truly new, independently authored
scenarios with paraphrases, negation, irony, emotion transitions,
mixed affect and protected identity challenges.
