# LLM_CHA v0.9.7.19 — Experience Conclusion & Dialogue Closure

A final short-lived `awaiting_conclusion` state is entered when the
second taste follow-up is consumed. The product name is cleared at that
time, preserving `product_context_present=false`.

Exactly the **next ordinary user utterance** may close the conversation
if it is a supported conclusion: `満足`, `満足した`,
`とても満足した`, `満足だった`, `よかった`, `良かった`,
`おいしかった`, or `美味しかった`.
Unrelated utterances consume the conclusion opportunity and follow normal
routing. Status checks do not consume it.

This is a narrow intent rule, not general understanding of sentiment.
Conclusions are not learned or saved to Semantic Memory.

## Windows verification

```powershell
git fetch origin
git switch --track origin/v0.9.7.19
python -m unittest -v test_clipboard_conclusion_v09719.py test_dialogue_lifecycle_gate_v09718.py test_clipboard_taste_dialogue_v09716.py
python chat.py
```

Then enter `/read-clipboard` after copying the menu, followed by:

```text
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだことがある
酸味と甘さのバランスが良かった
黒耳は、ブラックチョコレートで甘かった
/clipboard-dialogue-status
満足した
/clipboard-dialogue-status
```

Expected before conclusion: `awaiting_taste=false`,
`remaining_taste_turns=0`, `product_context_present=false`,
`awaiting_conclusion=true`.
Expected after: `awaiting_conclusion=false`.
