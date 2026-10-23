# LLM_CHA v0.7.32 — Trusted / Experimental GUI

The existing `chat_window_v061.py` Tkinter conversation mirror has
been updated in-place for LLM_CHA v0.7.32.

Changes:
- Shows live Trusted Semantic Memory internalized/pending counts.
- Shows Experimental restore, sleep and adapter reload state.
- Shows latest observed Candidate count and last routed evidence source.
- Keeps conversation-only message pane and LaTeX rendering.
- Retains **terminal input**; GUI is a read-only conversation mirror.
- Parses diagnostic status independently so runtime logs do not leak
  into the conversation pane.
- Status strings indicate runtime observations only and do not certify
  factual truth or auto-promote Candidate knowledge.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.7.32
python -m unittest -v test_gui_status_v0732.py test_chat_window_v061.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat_window_v061.py
```

Use the PowerShell/terminal for `/sleep` and chat input. The mirror
displays the assistant's responses and separate runtime status labels.
Closing the GUI retains the prior behavior: it does not forcibly
terminate the underlying `chat.py` process.
