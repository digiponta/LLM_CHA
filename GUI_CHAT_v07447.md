# LLM_CHA v0.7.44.7 — GUI-only chat

The original `chat.py` is preserved and runs as a single child process.
This Tkinter GUI gives a writable conversation input, rendered LaTeX
through the existing GUI helper, conversation-only output, and quick
`/sleep` / `/status` commands. The GUI runs the existing retrieval,
Wikipedia, memory, truth, and experimental routing in the same backend.
Quality gate is ON in the GUI child by default.

## PowerShell

```powershell
git pull
python -m unittest -v test_chat_gui_v07447.py
python chat_gui_v07447.py
```

Optional:

```powershell
python chat_gui_v07447.py --no-quality-gate
python chat_gui_v07447.py --model results/approved_paraphrase_v0743/experimental-trusted.pt
```

GUI limitations: persona-gap review is not a learned Japanese fluency model;
a low-signal answer falls back. The GUI does not automatically perform synonym
recovery or bounded regeneration. Command diagnostics are not displayed in the
conversation pane. This frontend has not yet been acceptance-tested on the
Windows GPU machine. No promotion of unverified facts occurs in this GUI layer.
