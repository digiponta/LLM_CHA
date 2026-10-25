# v0.9.7.5 — Explicit Clipboard Reading

Copy text yourself in a browser with Ctrl+A and Ctrl+C, then run
`/read-clipboard` in LLM_CHA. This works independently of Chrome CDP,
Google search, and browser-specific extensions.

```powershell
git fetch origin
git switch --track origin/v0.9.7.5
python -m unittest -v test_clipboard_browser_reader_v0975.py
python chat.py
```

Use:
1. Open a permitted public page in Chrome.
2. Select text with Ctrl+A, then Ctrl+C.
3. Switch to LLM_CHA and enter `/read-clipboard`.

Only the current clipboard text (maximum 12,000 characters) is displayed.
No automated Ctrl+A/Ctrl+C or site crawling is performed.
The URL cannot be reliably inferred from plain clipboard text and is
intentionally `null`. Content is untrusted and not persisted, approved
or trained. Beware of sensitive data in clipboard and terminal logs.

**Terms remain applicable:** copy/paste is not a workaround for
prohibited automated extraction or permission to train on others' text.
Google's automated search collection restrictions remain relevant.
