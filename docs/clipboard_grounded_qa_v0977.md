# LLM_CHA v0.9.7.7 — Clipboard Grounded QA

Extends manually copied page context to answer:
- `フードには何がある？`
- `フラペチーノの種類は？`
- `飲み物は何がある？`
- `おすすめは？` (explicitly declines evidence-free evaluations)

Retrieval uses section headings `ビバレッジ`, `フード` and the
corresponding `一覧へ` delimiters from the provided page text.
It de-duplicates exact repeated product names. Unrelated questions
continue through prior routing, including Wikipedia.
This is a simple evidence selection algorithm, not a general-purpose
LLM or semantic vector question answerer.

To test:

```powershell
git fetch origin
git switch --track origin/v0.9.7.7
python -m unittest -v test_clipboard_grounded_qa_v0977.py test_clipboard_context_v0976.py test_clipboard_browser_reader_v0975.py
python chat.py
```

Copy the Starbucks menu text with Ctrl+A, Ctrl+C, then enter
`/read-clipboard`, followed by each question.
Text remains EXTERNAL_UNVERIFIED, transient, and not trainable.
