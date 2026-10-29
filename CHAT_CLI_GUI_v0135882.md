# v0.13.58.82 — CLI / GUI Chat Refresh

Both entrypoints share existing `chat.py` inference and command handling. No retrieval, LLM_SEM score, or provisional AI-reviewed label is authorized for runtime answer reuse. The v0.13.58.81 verifier remains offline/experimental.

CLI:
```powershell
python chat.py
# then /status or /verifier-status
```

GUI:
```powershell
python chat_gui.py
```
GUI uses a subprocess and streams standard output without waiting for newlines (supports the bare `You> ` prompt). /status button is wired to a local status report and sends the same slash command to the CLI. Restart and clean shutdown are supported. The GUI requires tkinter and an environment capable of running `chat.py`, including its model/tokenizer dependencies. It is not a native embedded rendering of LaTeX, and does not introduce training or automatic answer approval.

Tests:
```powershell
python -m unittest -v test_chat_runtime_status_v0135882.py test_answer_reuse_verifier_v0135881.py test_answer_reuse_verifier_v0135880.py
```
