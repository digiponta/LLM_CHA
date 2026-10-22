# LLM_CHA GUI mirror v0.6.8

The launcher `chat_window_v061.py` keeps its filename for existing workflows.
It still uses terminal/PowerShell input and displays only user/AI conversation
in a separate read-only Tkinter window, including the optional LaTeX renderer.

New behavior: choose a checkpoint when launching the GUI. No model is changed
on disk, no automatic learning occurs, and `chat.py` is not modified.

```powershell
git fetch origin
git switch --track origin/v0.6.8
python -m unittest -v test_chat_window_v061.py test_gui_latex_v062.py test_chat_window_models_v068.py

# Existing/default runtime, unchanged:
python chat_window_v061.py

# Explicit checkpoint:
python chat_window_v061.py --model model/model-llm-cha-aozora-replay-v067-r2.pt --tokenizer model/tokenizer-v0.7-bpe.json

# Opt in to the most recent locally present experimental Aozora checkpoint:
python chat_window_v061.py --latest-experimental
```

Model selection preference for `--latest-experimental`: v0.6.7-r2,
v0.6.7, v0.6.5. The option requires local checkpoint files and
`model/tokenizer-v0.7-bpe.json`, otherwise startup fails with an explanation.
Default launch still delegates choice to `chat.py`.

The window title and header show the selected model basename.
Closing the window does not stop the CLI; exit the chat using `/exit`.
No claims are made that the experimental checkpoint passes persona or
Truth Gate regression; these features belong to the underlying `chat.py`.
