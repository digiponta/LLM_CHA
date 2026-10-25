# LLM_CHA v0.9.7.10 — Compact Clipboard GUI

The CLI `chat.py` retains its full JSON diagnostic response. The Tk
mirror `chat_window_v061.py` replaces only successful clipboard-read
JSON with a short confirmation (length, transient context, unverified).
Other assistant messages continue unchanged, including follow-up QA.
A malformed or unexpected clipboard payload is shown instead of silently
discarded.

```powershell
git fetch origin
git switch --track origin/v0.9.7.10
python -m unittest -v test_gui_clipboard_display_v09710.py test_gui_clipboard_button_v0979.py
python chat_window_v061.py
```

In Chrome copy the desired Web text (Ctrl+A/Ctrl+C); click
`クリップボード読込`, then ask `メニューは`. The GUI should show a brief
clipboard confirmation and the grounded answer instead of the long JSON.
CLI mode remains verbose. No Web knowledge is automatically approved,
stored or learned.
