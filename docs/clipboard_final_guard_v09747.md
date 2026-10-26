# LLM_CHA v0.9.7.47 — Clipboard Final Answer Guard

Extends the opt-in \`--final-guard\` to the early
\`CLIPBOARD_CONTEXT_ANSWER\` branch in chat.py.

Observed failure reproduced:
- User: ハム&ゴーダチーズ スターバックス バゲットサンドを食べた
- Existing clipboard answer: そう、ハム&ゴーダチーズ スターバックス バゲットサンドを飲んだのね。どんな味だった？
- Proposed corrected answer: そう、ハム&ゴーダチーズ スターバックス バゲットサンドを食べたのね。どんな味だった？

Correction uses an exact, overlapping food name and explicitly
stated user action. The guard does not infer unverified source facts,
does not write training data, and keeps source truth_state
EXTERNAL_UNVERIFIED.

\`chat.py\` uses the guard **only if enabled**, preserving default
behavior. All existing generation quality safeguards remain in place.
This is a small lexical safety check, not a universal verb ontology.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.47
python -m unittest -v test_clipboard_final_guard_v09747.py test_final_answer_guard_v09746.py
python chat_window_v061.py --final-guard
\`\`\`

Run the prior clipboard workflow again and check the terminal route
and \`clipboard_final_guard=REJECT\` diagnostic. Rejected clipboard
outputs are not automatically promoted to trusted memory. The GUI
continues to mirror the child process and the existing semantic
preview is read-only.

Note: The current guard focuses on user-stated 食べた/飲んだ and
specific food/drink item endings. Broader linguistic actions,
negation scopes, long compound names and quoted text need independent
holdout tests before expansion.
