# LLM_CHA v0.9.7.58 GUI Update

This branch extends v0.9.7.58. The GUI uses the **same** chat.py subprocess and /read-clipboard operation as CLI. The existing button sends /read-clipboard. The GUI retains a compact summary instead of displaying the full clipboard JSON.

Changes:
- Update GUI version indicator to v0.9.7.58.
- Highlight clipboard-sourced unverified answers separately from normal assistant replies.
- Add scoped GUI clipboard and route regression tests.

## Local Windows verification

```powershell
git fetch origin
git switch v0.9.7.58-gui
git pull --ff-only
python -m unittest -v test_chat_window_v061.py test_gui_clipboard_v09758.py test_clipboard_evidence_binding_v09757.py test_topic_clipboard_bridge_v09758.py
python chat_window_v061.py
```

In GUI, use the Google search request to open the browser, copy the results with Ctrl+A / Ctrl+C, press クリップボード読込, then ask スファレライトの成分は and 化学組成を知りたい. Expect ZnS with the label クリップボード由来・未検証.

No model training or auto-promote is performed by this display path. The target-machine end-to-end test still needs to be run.
