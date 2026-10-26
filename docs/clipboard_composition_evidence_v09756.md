# v0.9.7.56 — Source-grounded Clipboard Composition

Temporary per-clipboard `CompositionContext` records the mineral topic and attribute (`化学組成`). It is attached to `ClipboardContext` and runs before generic dialogue answers.

When the copied page contains nearby **スファレライト / 閃亜鉛鉱 / sphalerite** and the phrase **硫化亜鉛（ZnS）**, the response cites only the clipboard text and explicitly labels it **未検証**. Queries such as 「スファレライトの成分は」「化学組成を知りたい」 and later repeated queries preserve the topic across unrelated preference/evaluation turns. A new clipboard or clear resets the state. If evidence is missing, do not invent ZnS.

This is narrow experimental evidence matching, not independent source validation or general chemistry question answering. No Semantic Memory promotions or model training.

## Windows commands

```powershell
git fetch origin
git switch --track origin/v0.9.7.56
python -m unittest -v test_clipboard_composition_evidence_v09756.py
python chat_window_v061.py --final-guard --gui-only-input
```

Expected: 9 new unit tests. Verify with the actual copied page that it contains the stated evidence (otherwise the conservative missing-evidence response is correct).
