# LLM_CHA v0.9.7.53 — Incomplete Utterance Gate

Under opt-in \`--final-guard\`, the runtime detects conservative
Japanese topic fragments that end with particles (は、が、を、に、
へ、と、も、で) before the general semantic/Wikipedia fallback.

- 「満足は」 → 「満足について、何を知りたい？」
- 「満足とは」 → existing Definition Intent Resolution
- 「満足」 → existing short evaluation
- 「満足は大切」 → existing dialogue/knowledge path
- 「/exit」 → normal command processing

This is deliberately bounded syntactic detection. It does not claim
to understand incomplete syntax generally. Questions, quoted clauses,
multi-clause statements, long utterances, and uncertain contexts are
not intercepted. These response shortcuts do not promote, persist
or train anything.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.53
python -m unittest -v test_incomplete_utterance_v09753.py test_definition_intent_v09752.py test_conversational_intent_v09751.py
python chat_window_v061.py --final-guard --gui-only-input
\`\`\`

Expected 28 tests (9 new + 9 + 10). Confirm the GUI routes for
「満足」「満足とは」「満足は」. Wikipedia relevance filtering
remains a separate unresolved task; this guard avoids only selected
unfinished utterances entering the search path.
