# LLM_CHA v0.9.7.13 — Structured Evidence Association

This revision replaces the nearby-paragraph heuristic in
`clipboard_context_expansion_v09712.py` with a stricter rule:

- Prefer exact case-insensitive heading matches appearing in the question.
- Attach a description only if it **immediately follows** the heading
  as the next nonempty line and is at least 75 characters long.
- Do not reuse a description twice in the answer.
- Keep quotations unverified, transient and excluded from model training.

The strict adjacency rule deliberately favors precision over recall. Pages
whose headings and descriptions are separated by navigation, metadata, or
several paragraphs may not have a description attached. It is not an HTML
structural parser or semantic entailment model.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.13
python -m unittest -v test_clipboard_structured_association_v09713.py test_clipboard_context_expansion_v09712.py test_clipboard_generic_evidence_v09711.py
python chat_window_v061.py
```

In the GUI, copy the WIZG.org research introduction and use the clipboard
read button, then ask:
```text
このページでQuantum Hyper-Aetherについて記述は？
このページでSemantic Operating Systemsについて記述は？
```
Each answer should include one exact heading, its adjacent explanation,
and no repeated quotation.
