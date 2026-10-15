# LLM_CHA v0.6.1 — GUI Conversation Mirror

Release date: 2026-10-15
Base: v0.6.0 Wikipedia Grounded Dialogue Baseline

## Highlights

- Optional Tkinter GUI displays user questions and AI answers in chronological order.
- The existing `chat.py` command-prompt interface remains the input and diagnostic interface.
- Windows Unicode console input relay uses `ReadConsoleW`, while child process pipes use UTF-8.
- Duplicate adjacent `You> ` prompts are filtered in the CLI relay.
- The launcher closes the GUI automatically when `chat.py` exits via `/exit`.
- The v0.6.0 Wikipedia evidence-grounded conversational features are retained unchanged.

## Scope and safeguards

- The graphical window is a **read-only conversation mirror**, not an alternate chat input.
- Operational commands, diagnostic lines, and learning controls stay on the CLI.
- Wikipedia evidence retains the external-unverified safety policy: `EXTERNAL_UNVERIFIED`, `train_ready=False`, `auto_promote=False`.
- No automatic saving of chat history is introduced.

## Verification evidence

- The user reported three passing GUI parser tests for the first v0.6.1 implementation.
- Subsequent Windows runtime logs confirmed Japanese Wikipedia responses were generated through the launcher after Unicode input fixes.
- The user reported that `/exit` returned to the PowerShell prompt.
- A full rerun of the final six GUI tests was **not** provided; do not claim six of six PASS.
- The inherited Wikipedia test suite passed 60/60 in v0.6.0, before GUI changes.

## How to run

```powershell
git fetch origin
git switch v0.6.1
git pull --ff-only origin v0.6.1
python -m unittest -v test_chat_window_v061.py
python chat_window_v061.py
```

Use the command prompt for questions and commands; type `/exit` to quit.

## Known limitations / next steps

- Final graphical window behavior, prompt filtering, and all six GUI regression tests should be verified on Windows.
- The GUI does not implement conversation save/search or editable input controls.
- Evidence ranking, semantic duplicate detection, response formatting, and multi-article context management remain future improvements.
