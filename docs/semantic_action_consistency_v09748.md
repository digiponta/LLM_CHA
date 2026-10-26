# v0.9.7.48 — Semantic Action Consistency (bounded experiment)

This branch adds an experimental subject/action/object representation
for short Japanese past-tense user statements and answers. It parses
one clause only, checks object identity, action labels and negation,
and prefers explicit user-reported actions over a conflicting answer.

Example:
- USER: ハム&ゴーダチーズ スターバックス バゲットサンドを食べた
- GENERATED: そう、ハム&ゴーダチーズ スターバックス バゲットサンドを飲んだのね。どんな味だった？
- CHECK: same object, EAT != DRINK, explicit USER_UTTERANCE wins
- REPAIRED: そう、ハム&ゴーダチーズ スターバックス バゲットサンドを食べたのね。どんな味だった？

Other limited pairs: BUY/BORROW and SEE/HEAR, plus negation
differences within the same verb. Unsupported or ambiguous input
is REVIEW; automatic repair is not allowed unless item identity
and mismatch are explicit. It is not a full Japanese semantic parser.

Integrated into the opt-in --final-guard clipboard route before
legacy v0.9.7.47 food/drink checks. The original
EXTERNAL_UNVERIFIED source state remains unchanged. No Semantic
Memory promotion, model training or chat history rewriting.

## Windows PowerShell
\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.48
python -m unittest -v test_semantic_action_consistency_v09748.py test_clipboard_final_guard_v09747.py test_final_answer_guard_v09746.py
python chat_window_v061.py --final-guard
\`\`\`

Inspect the clipboard diagnostic. With the new semantic path it
reports reason=semantic-action-consistency rather than the earlier
explicit-user-action-conflict for supported statements.
Review precision and recall on genuinely independent multi-clause
and negated-scope dialogues before expanding automatic replacements.
