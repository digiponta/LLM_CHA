# LLM_CHA v0.9.7.50 — Personal Preference Intent + GUI Input Isolation

The runtime now has an **opt-in** personal-preference detector,
executed before the bare-concept semantic/unknown knowledge route,
when \`--final-guard\` is enabled.

Examples:
- 「ハム&ゴーダチーズ スターバックス バゲットサンドも好き」
  → 「ハム&ゴーダチーズ スターバックス バゲットサンドも好きなんだね。」
- 「ラテが好き」 → personal preference statement
- Questions, contrastive and ambiguous statements are not intercepted.
- Never writes to Semantic Memory, updates model weights, or treats
  personal preference as verified general knowledge.

The existing Tkinter chat mirror now supports \`--gui-only-input\`
to disable terminal keyboard forwarding and avoid the observed mixing
of console input and diagnostic stdout. It still prints diagnostics
to the launching console; use GUI for message submission.
The existing \`chat.py\` process, model and output parsing remain.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.50
python -m unittest -v test_preference_intent_v09750.py
python chat_window_v061.py --final-guard --gui-only-input
\`\`\`

The test suite does not certify natural Japanese coverage or a
comprehensive speaker/coreference parser. Preference extraction is
intent-only, transient and non-persistent.
