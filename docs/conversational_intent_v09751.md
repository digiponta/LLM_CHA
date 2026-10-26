# LLM_CHA v0.9.7.51 — Short evaluations and actions

With \`--final-guard\`, the runtime uses a bounded conversational
detector for short evaluations (満足、美味しかった、いまいち、微妙だった)
and simple actions (食べた/食べなかった、飲んだ/飲まなかった、
行った、買った、見た、聞いた、読んだ). These are
USER_UTTERANCE intents, not verified knowledge. No auto learning.

**Explicit priority:** Any user utterance containing the literal
「とは」 bypasses the clipboard-answer and daily/preference-intent
shortcuts and remains available to the existing knowledge/search
routing. This is a search *intent* preference; the response still
depends on existing routing and source availability. It does not
guarantee that an external page is fetched.

## Windows PowerShell
\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.51
python -m unittest -v test_conversational_intent_v09751.py test_preference_intent_v09750.py
python chat_window_v061.py --final-guard --gui-only-input
\`\`\`

Try 「満足」, 「美味しかった」, 「ケーキを食べた」,
「コーヒーを飲まなかった」 and 「満足とは」. The last one
must not show route CONVERSATIONAL_INTENT or CLIPBOARD_CONTEXT_ANSWER.

Limitations: short lexical patterns only; questions, quoted text,
multi-clause utterances and long complex statements fall through to
normal handlers. No model checkpoint or Semantic Memory edits.
