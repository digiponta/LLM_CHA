# LLM_CHA v0.4.22 — Labeled Response Quality Benchmark

Purpose: compare v0.4.21 Shadow Evaluation warnings with human judgments of answer appropriateness, without changing runtime answers.

## Data contract

UTF-8 JSONL; one object per line, exactly these fields:
- `id`: unique nonempty ID;
- `split`: `development` or `holdout`;
- `question`, `answer`: original query and response;
- `gold_inappropriate`: true if the response is **inappropriate** for the question, false otherwise (gold label);
- `agreement` and `semantic_agreement`: frozen [0,1] model diagnostics;
- `runtime_accepted`: original live decision, kept unmodified;
- `label_source`: `DEVELOPMENT_EXAMPLE` or `HUMAN_REVIEW` (holdout requires the latter).

The supplied `fixtures/persona_quality_development_v0422.jsonl` contains **two already-used cases** from the experimental history, not independent validation. These labels are illustrative development judgments, not a substitute for blinded annotation. **No real independent holdout is bundled.** Holdout independence must be established from provenance, sampling and pre-registration outside the script. The output intentionally never claims independently validated status.

## Metrics

- TP: warning on an inappropriate answer
- FP: warning on an appropriate answer
- TN: no warning on an appropriate answer
- FN: no warning on an inappropriate answer
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- False Positive Rate = FP / (FP + TN)
- False Negative Rate = FN / (FN + TP)
- Accuracy = (TP + TN) / total

Undefined rates have JSON null values, not fabricated zeros. Both warning and no-warning decisions are computed using **unaltered v0.4.21 criteria**. Evaluation is read-only; this code does not modify `chat.py`, Truth Gate, model weights, Semantic Memory, Wikipedia, `/sleep`, or `/train`.

## Run on Windows / PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_quality_benchmark_v0422.py test_persona_response_shadow_v0421.py test_persona_dialogue_intent_v0420.py
python persona_quality_benchmark_v0422.py --dataset fixtures/persona_quality_development_v0422.jsonl --split development
python persona_quality_benchmark_v0422.py --dataset fixtures/persona_quality_development_v0422.jsonl --split holdout
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Expected: development count=2 with TP=1 and FP=1 (and Precision=0.5), while holdout reports count=0, NO_LABELED_SAMPLES, and null metrics. Such development figures **must not be reported as generalization accuracy**.

## Next experiment

Collect new, untouched, diverse generated question-answer examples (including ambiguous, well-formed, persona, topic, and knowledge cases), record frozen agreement diagnostics, obtain blinded human labels with a written rubric, and seal a distinct holdout prior to choosing thresholds. Measure per-intent performance, label disagreement, sample sizes, confidence intervals, and appropriate-answer false warnings. No gate enforcement until separately validated.
