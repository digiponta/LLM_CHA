# LLM_CHA v0.9.7.52 — Definition Intent Resolution

A narrowly scoped definition-intent layer is available under the
existing opt-in \`--final-guard\`. Literal 「とは」 is still treated
as a definition/search request, not a short daily evaluation.

- 「満足」 → conversational evaluation (previous route).
- 「満足とは」 → LOCAL_CURATED definition:
  「満足とは、期待や欲求が満たされ、十分だと感じる状態のことです。」
- 「量子力学とは」 → existing knowledge/search pipeline;
  the experimental module makes no unsupported definition assertion.

The \`is_relevant_definition\` utility refuses known indicators of a
disambiguation page and nonmatching article titles. It is provided
for future retrieval integration: the existing Wikipedia rendering
pipeline is NOT yet globally filtered by this utility. Even when a
candidate passes, the text is not automatically verified or learned.
The local curated response is not a live Internet lookup; it is a
small source-labelled definitional example. For novel terms, the
existing search path is preserved.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.52
python -m unittest -v test_definition_intent_v09752.py test_conversational_intent_v09751.py
python chat_window_v061.py --final-guard --gui-only-input
\`\`\`

Expected 19 tests (9 new + 10 existing). Check 「満足」 versus
「満足とは」. No checkpoint, training, or Semantic Memory changes.

Further work: genuinely connect article relevance filtering to all
Wikipedia fallback routes, resolve word sense using provenance,
and compare against independent definition-question holdouts.
