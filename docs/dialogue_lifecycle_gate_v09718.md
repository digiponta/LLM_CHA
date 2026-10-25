# LLM_CHA v0.9.7.18 — Dialogue Lifecycle and Gate Regression

- Clear `experience_product` once the last taste response consumes the two-turn budget.
- Existing topic-switch and fresh clipboard resets remain unchanged.
- Add six regression tests: lifecycle expiry, topic switch, clipboard reload,
  observed extreme lexical/semantic disagreement, normal semantic rescue, and
  ordinary lexical acceptance.

This version does not modify the generation model or retrain weights.
The gate threshold of 0.05 remains experimental; these tests validate
mechanics, not empirical false-acceptance/false-rejection rates.

## Windows verification

```powershell
git fetch origin
git switch --track origin/v0.9.7.18
python -m unittest -v test_dialogue_lifecycle_gate_v09718.py test_extreme_probe_disagreement_v09717.py test_clipboard_taste_dialogue_v09716.py
python chat.py
```

Following `/read-clipboard`, reproduce the user report and two taste
responses; `/clipboard-dialogue-status` should end with
`awaiting_taste=false`, `remaining_taste_turns=0`, and
`product_context_present=false`.

Future work: run held-out known/unknown Japanese answer samples through the
full runtime and compare false accepts, false rejects, and coverage against
v0.9.7.16. Unit tests do not replace that evaluation.
