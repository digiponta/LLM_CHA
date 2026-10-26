# v0.9.7.56 Topic-Keyed Context (experimental)

Opt-in via `--final-guard`; conversation-local topic-to-attribute entries.

- 「スファレライトの成分は」 → confirms topic and chemical composition attribute.
- 「化学組成を知りたい」 → reuses the active topic.
- Intermediate preference/evaluation utterances do not erase the topic.
- 「スファレライトの成分」 also refreshes an explicit topic query.
- 「とは」 and commands stay with their existing routing.
- Evidence status remains `SOURCE_NEEDED`; no formula is invented,
  no training or Semantic Memory promotion.
- This version does **not** perform evidence extraction from pasted
  content. That is a separate future integration.

```powershell
git fetch origin
git switch --track origin/v0.9.7.56
python -m unittest -v test_topic_keyed_context_v09756.py
python chat_window_v061.py --final-guard --gui-only-input
```

Eight new tests. Regression expectations are limited to these simple
chemical-composition phrasing patterns; full semantic coreference and
multi-intent arbitration remain future work.
