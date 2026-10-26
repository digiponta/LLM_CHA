# LLM_CHA v0.9.7.46 — Opt-in Final Answer Guard

This incremental experiment adds an **opt-in** final-answer guard to
\`chat.py\`. It does not retrain checkpoints or modify Semantic Memory.

Supported probes:
- 「満足した」 is treated as a daily satisfaction statement rather than
  a bare unknown concept and Wikipedia ambiguity lookup.
- The observed broken text 「長門有希丘陵、瀬料水産基地)。」 is rejected
  with a neutral clarification.
- An obviously mismatched food item like
  「バゲットサンドを飲んだ」 is corrected to 「食べた」.
- Unrecognized output remains REVIEW, never declared fully verified.

The guard is deliberately narrow. It is **not a language parser** and
does not assess arbitrary food/drink ontology or every model response.
Clipboard-context routing runs earlier and still bypasses this
experimental guard. GUI annotations are separate and read-only.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.46
python -m unittest -v test_final_answer_guard_v09746.py test_gui_semantic_preview_v09745.py
python chat_window_v061.py --final-guard
\`\`\`

Alternatively, after launch, type one of:
- \`/final-guard-on\`
- \`/final-guard-off\`
- \`/final-guard-status\`

For a targeted CLI probe:
\`\`\`powershell
python chat.py --final-guard
\`\`\`
Try 「満足した」 and confirm \`DAILY_SATISFACTION\` route.
The GUI itself retains the prior version title and read-only
Semantic annotation widget pending a dedicated synchronized UI release.

Guard rejection in MODEL_GENERATION sets \`accepted=False\`, preventing
registration as a trusted accepted conversation turn. The daily route
does not automatically persist knowledge. Do not infer heldout quality
from this small collection of known failure examples.

## Follow-up limitations

- Validate handling of food/drink verbs for clipboard-grounded answers.
- Incorporate actual dialogue intent before routing bare concepts.
- Compare guard performance on separately heldout natural dialogue.
- Confirm historical internalized=0 pending=56 against specific model
  checkpoint and Semantic Memory data stores before running /sleep.
