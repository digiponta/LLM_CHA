# v0.9.7.16 — Product Taste Dialogue State

Adds a transient, two-follow-up-turn taste state to the existing ClipboardDialogue.
After an exact source product is recognized in a first-person experience report,
taste statements are answered conversationally rather than dispatched to the
general checkpoint (which previously produced unrelated garbled text).

- `飲んだことがある` -> ask about taste, remember the named product transiently.
- `酸味と甘さのバランスが良かった` -> acknowledge and follow up.
- `黒耳は、ブラックチョコレートで甘かった` -> acknowledge the chocolate note.
- Unrelated questions pass to the existing clipboard evidence/QA routes.
- New clipboard reads reset experience context; after two taste replies it expires.
- This is a narrow rule-based dialogue fallback, **not** improved LLM
  generation or factual verification; personal experience is not trained
  or automatically promoted to Semantic Memory.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.16
python -m unittest -v test_clipboard_taste_dialogue_v09716.py test_clipboard_dialogue_intent_v09715.py
python chat_window_v061.py
```

Copy the same Starbucks menu into clipboard and replay the original
first-person report and two follow-up taste utterances.
