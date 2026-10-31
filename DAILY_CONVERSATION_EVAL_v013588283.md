# v0.13.58.82.83 — Daily Conversation Baseline Evaluation

Scope deliberately reduced to five questions. This release **does not train, fine-tune or alter** the LLM. It records the actual observed bad response as a baseline, and lets us measure changes without confusing safety-gate behavior with fluent generation. The 5 questions are evaluation-only. The `example_acceptable` strings are examples for human grading, **not** answers to be returned by a template and **not** new training examples.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.83-daily-conversation-eval
python -m unittest -v test_daily_conversation_eval_v013588283.py test_response_quality_guard_v013588282.py

python daily_conversation_eval_v013588283.py --observations data/daily_conversation_baseline_observed_v013588283.json --output results/daily_baseline_v013588283.json
python chat.py
```

Try the five evaluation questions in `data/daily_conversation_eval_v013588283.json` one at a time. Record **actual** raw candidate, displayed answer, and gate route. Do not add these evaluation questions or example answers to training data. Record new results as a distinct JSON file (same `runs` structure) and compare using:
```powershell
python daily_conversation_eval_v013588283.py --observations results/daily_after_observed_v013588283.json --output results/daily_after_report_v013588283.json
```

The evaluator reports only observed count, surface defects, and fallback rate. A superficially usable answer always requires human review for conversational appropriateness. Empty/missing cases remain NOT_RUN. There is no claim of model quality improvement until a separate, controlled training experiment and independent holdout test have actually run. The next step is to identify a **separate** tiny training dataset without contaminating these holdout questions.
