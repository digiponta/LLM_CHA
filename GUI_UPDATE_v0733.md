# LLM_CHA v0.7.33 — Interactive GUI and runtime status

- Updated existing `chat_window_v061.py`, preserving its launcher name.
- Two-row status display prevents the last route from overflowing a single line.
- Restored Experimental Candidate count is displayed from `chat.py` startup metadata.
- Input box + Enter/Send and a `/sleep` button relay commands to the existing chat process.
- Existing terminal keyboard input stays available; both paths serialize child stdin writes.
- The conversation pane still filters diagnostic lines and preserves LaTeX rendering.
- Route indicators reflect evidence provenance and do not change Trusted/Experimental safety gates.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.33
python -m unittest -v test_gui_status_v0732.py test_gui_status_v0733.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat_window_v061.py
```

Expected new status tests: 5; previous status tests: 7. The GUI still uses
`chat.py` as the single process owning training and inference; it does
not directly alter Candidate or Approved stores. Closing the window
does not automatically stop the CLI conversation. The GUI /sleep action
is intentional and can train PENDING Experimental candidates according
to the existing runtime policy.
