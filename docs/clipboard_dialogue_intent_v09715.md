# v0.9.7.15 — Clipboard conversational intent

Adds conservative transient intent handling **before** existing clipboard QA
and Wikipedia fallback:

- “スターバックスのメニューは” with a copied beverage/food menu sets
  one-turn `awaiting_category` and asks for a choice.
- “ドリンク” or “フード” on the next turn resolves that choice from copied
  source; without an awaiting menu prompt those short utterances are not forced.
- First-person experience mentioning an exact product name (e.g.
  “黒耳 ver.は、飲んだことがある”) produces a follow-up question instead
  of reprinting the Frappuccino catalogue.
- “ぐぐって” and “ググって” both trigger explicitly requested browser search.

This is deliberately rule-based and narrow, not general semantic intent
recognition. No persistent personal memory and no automatic learning.
The earlier `/clipboard-generate` diagnostic is unchanged.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.15
python -m unittest -v test_clipboard_dialogue_intent_v09715.py test_clipboard_grounded_generation_v09714.py test_clipboard_structured_association_v09713.py
python chat_window_v061.py
```

Read a copied Starbucks menu using the clipboard button and try:
```text
スターバックスのメニューは
ドリンク
フラペチーノの種類は
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.は、飲んだことがある
```
