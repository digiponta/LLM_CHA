# GUI update — v0.9.7.45 Semantic Preview

The original \`chat_window_v061.py\` has been updated to launch the
existing \`chat.py\` CLI and show a **read-only** Semantic Quality +
Japanese Repair diagnostic under generated answers. A checkbox toggles
these annotations. Normal input, status display, LaTeX and source
formatting continue to use the original GUI.

**Important separation:** the subprocess chat.py reply, its conversation
history, checkpoint, Semantic Memory and approval gates are unchanged.
The GUI shows potential corrected replies with the explicit label
「修正候補（未送信）」, not as if the model produced them. This avoids
desynchronizing the model's actual history and the displayed conversation.
The GUI does not auto-promote, automatically train or persist proposals.

## Windows PowerShell

\`\`\`powershell
git pull origin v0.9.7.45
python -m unittest -v test_gui_semantic_preview_v09745.py test_japanese_repair_gate_v09745.py
python chat_window_v061.py
\`\`\`

The *GUI application* is \`chat_window_v061.py\`, not \`chat.py\` itself.
It runs chat.py in a subprocess. Use \`--model PATH --tokenizer PATH\`
to choose an explicit model, or leave it at the existing stable default.
Latest experimental Semantic states are quality-control sidecars,
not new learned weights.

## Known limitations

- Quality annotation is triggered on initial single-line \`AI> ...\`
  text. When answers span multiple lines, annotations may not cover
  every part; diagnostics aren't evidence of grammatical correctness.
- CLI typing directly into the terminal is still supported; the
  GUI-side annotation needs the associated user utterance to be
  visible in the GUI event stream.
- An ABSTAIN means the separate Semantic logic has no validated plan;
  the existing CLI answer remains displayed without endorsement.
- A future opt-in integration into actual runtime requires aligning
  the selected answer with conversational history and source tracking.
