# GUI chat.py with Semantic Reconciliation (experimental)

The new `chat_gui_v0119.py` is a Tkinter frontend for the existing `chat.py`.
It launches `chat.py` as a child process with `LLM_CHA_RECONCILIATION=1`.
Model/knowledge logic stays in `chat.py`, including existing Truth Gate and
Unknown rejection.

```powershell
git pull --ff-only
python -m py_compile chat_gui_v0119.py chat.py
python -m unittest -v test_chat_gui_v0119.py test_chat_semantic_reconciliation_v0119.py
python chat_gui_v0119.py
```

When `chat.py` asks `Decision [prefer_a/prefer_b/both_contextual/neither/skip]>`,
click a corresponding button, or type the decision in the input box.
After `both_contextual`, enter a distinguishing condition in the input box
at the `Context>` prompt. This UI redirects console prompts and output;
it does not introduce an independent semantic memory or approval mechanism.

The former `chat_window_v061.py` was not found in the connected branch, so
it was not overwritten. This frontend is new and experimental. A user must
test the real GUI on Windows; automated tests only check import/contract,
not interactive Windows rendering.
