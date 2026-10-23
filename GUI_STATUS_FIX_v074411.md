# v0.7.44.11 — GUI Status button fix

The original GUI button sent `/status`, but `chat.py` handles
`/semstatus` and `/sleep status` instead. The conversation parser
also intentionally suppresses command diagnostics. The replacement
button is **状態確認** and opens a read-only pop-up containing the
multiline `/semstatus` output. The status capture ends at the next
`You> ` prompt and is limited to 50,000 characters.

```powershell
git pull
python -m unittest -v test_gui_command_capture_v074411.py test_gui_status_button_v074411.py test_chat_gui_v07447.py
python chat_gui_v07447.py
```

Click 状態確認. A popup with actual backend output should appear.
The backend does not change Semantic Memory or Checkpoint during status.
This has not yet been tested on the user's Windows/GPU machine.
