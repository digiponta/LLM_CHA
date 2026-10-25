# LLM_CHA v0.9.3 — Topic Suggestion Follow-ups

This release adds a short-lived topic suggestion list in the active chat
session. It resolves ordinal follow-ups *before* default Wikipedia subject
routing and retrieves excerpts from `data/data-nagato.txt`.

```powershell
git fetch origin
git switch --track origin/v0.9.3
python -m unittest -v test_topic_suggestion_followup_v093.py test_topic_suggestion_v092.py test_corpus_answer_plan_v091.py
python chat.py
```

Manual runtime dialog:
- 量子力学的な話題は
- 最初の話題について教えて
- 2番目の話題を教えて
- 数学とは

Expected: first follow-up resolves to `粒子と波動` and uses
`TOPIC_FOLLOWUP_CORPUS` without a Wikipedia ambiguity menu.
The corpus passage is explicitly unverified. This feature currently
uses simple string-matched evidence; it does not generate a new science
explanation. Repeated and cross-topic follow-ups require additional tests.
No Semantic Memory or weights are modified.
