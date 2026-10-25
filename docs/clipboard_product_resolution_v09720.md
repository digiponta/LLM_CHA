# LLM_CHA v0.9.7.20 — Product Entity Resolution & Experience Intent

The clipboard menu dialogue now handles ordinary past tense and short
product aliases, without routing taste statements to the pretrained
LLM's generic generation path.

- The locally copied menu remains the sole source of valid product names.
- `黒耳` and `白耳` aliases resolve only when a matching product is present
  in the copied beverage/food sections.
- `黒耳を飲んだ` and full product names followed by `を飲んだ` initiate
  an experience conversation.
- `黒耳は、ブラックチョコレートで甘かった` can start a taste
  discussion even if there was no earlier experience turn.
- If the utterance matches multiple source products, request clarification
  rather than making a guess.
- During an existing taste discussion, a follow-up that repeats `黒耳`
  does not restart the two-turn counter.
- Existing knowledge QA, source citation mode, conclusion status, and
  model safety gate are preserved. No self-learning is performed.

The resolver is intentionally narrow and heuristic; it is not general
Named Entity Recognition or an LLM-based semantic parser.

## Windows
```powershell
git fetch origin
git switch --track origin/v0.9.7.20
python -m unittest -v test_clipboard_product_resolution_v09720.py test_clipboard_conclusion_v09719.py test_clipboard_taste_dialogue_v09716.py
python chat.py
```

After loading the Starbucks menu, test `黒耳を飲んだ`,
`黒耳は、ブラックチョコレートで甘かった`, and
`黒耳と白耳を飲んだ`.
