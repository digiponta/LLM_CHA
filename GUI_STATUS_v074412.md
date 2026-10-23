# LLM_CHA v0.7.44.12 — Expanded GUI status

The GUI now offers two read-only status commands:
- Semantic状態 — `/semstatus`
- 学習状態 — `/sleep status`

Both display raw `chat.py` diagnostic output in a dedicated popup. Concurrent status requests are disallowed. A missing response triggers a visible warning after 20 seconds. Neither command writes to Semantic Memory nor modifies model weights.

## Windows PowerShell

```powershell
git pull
python -m unittest -v test_gui_command_capture_v074411.py test_gui_status_button_v074411.py test_gui_status_v074412.py test_chat_gui_v07447.py
python chat_gui_v07447.py
```

Limitations: command status is captured until the next `You> ` prompt. A chat.py run that takes longer than 20 seconds may trigger a premature timeout. Do not issue a separate user command while a status response is pending. Confirm on the actual Windows/GPU machine.
