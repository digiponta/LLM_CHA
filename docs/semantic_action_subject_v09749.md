# LLM_CHA v0.9.7.49 — Subject-aware Semantic Action Gate

Experimental, conservative extension of v0.9.7.48.

- Recognizes a narrow set of explicit speakers and actors: 私/僕,
  友人, 彼, 彼女, 母. If omitted, subject is UNSPECIFIED, **not** USER.
- Compares subject, action, object, and negation before touching verbs.
- Different explicitly named subjects, object mismatch, quotation,
  multi-clause or unclear coreference → REVIEW, no automatic rewriting.
- Only single, lexically supported action statements may be REPAIR.
- Unchanged source trust policy; training and auto promotion disabled.
- Adds the opt-in subject-aware check to MODEL_GENERATION before the
  existing v0.9.7.46 final quality guard; the clipboard route also
  attempts subject-aware checks before the previous guards.
- Changes to a generated answer in MODEL_GENERATION mark accepted=False
  so altered answers are not treated as trusted accepted history.

This does **not** constitute broad Japanese language understanding,
and a REVIEW is not proof of quality. For clipboard follow-up sentences
with additional natural dialogue text, the prior v0.9.7.47 action
checks remain relevant.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.49
python -m unittest -v \`
  test_semantic_action_subject_v09749.py \`
  test_semantic_action_consistency_v09748.py \`
  test_clipboard_final_guard_v09747.py \`
  test_final_answer_guard_v09746.py
python chat_window_v061.py --final-guard
\`\`\`

Expected: 31 tests (10 new + 21 previous). Run a real-world GUI
comparison with an explicit actor and an intentionally conflicting
model answer. No model retraining is necessary.

Future work: quote/negation scope, true reference tracking across
dialogue turns, time and tense, causality and source provenance,
as well as an independent held-out evaluation before expanding
autonomous repair coverage.
