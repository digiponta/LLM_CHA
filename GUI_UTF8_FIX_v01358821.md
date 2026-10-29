# v0.13.58.82.1 — UTF-8 + Chat-first GUI fix

This fixes Windows GUI input/output mojibake by setting `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and `LLM_CHA_GUI_UTF8=1` on the subprocess, while preserving native CLI encoding when invoked without the GUI flag.

The conversation tab shows only user/AI turns; startup help, command lists, prompts, traces and status output remain available in **ログ・コマンド**. The GUI does not claim to reproduce an unavailable historical GUI source exactly; it restores a clean chat layout while retaining the existing subprocess runtime and model.

PowerShell:
```powershell
git fetch origin
git switch v0.13.58.82.1-gui-utf8-layout-fix
python -m unittest -v test_chat_gui_utf8_v01358821.py test_chat_runtime_status_v0135882.py
python chat_gui.py
```

Test Japanese input (`こんにちは`) and inspect the log tab for `[normalized input]` and model response. If the answer remains malformed after input/output transport is fixed, investigate model/tokenizer or normalization separately. The UI does not enable experimental automatic Answer Reuse.
