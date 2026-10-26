# v0.9.7.63 — Japanese sentence-final の fix

A causal question `なぜカットが難しいの？` was being misread as a possessive subject because the previous regular expression matched any preceding text before `の`. It incorrectly rejected the active topic.

Fix: only parse an explicit subject when `の` precedes a known attribute or causal object (e.g. `スファレライトのカット`); otherwise use the active topic. The selected causal passage remains source-literal and unverified.

## Windows verification

```powershell
git fetch origin
git switch v0.9.7.63
git pull --ff-only
python -m unittest -v test_causal_ellipsis_v09763.py test_clipboard_causal_evidence_v09762.py
python chat_window_v061.py
```

Copy the search page, use the clipboard read control, then ask `なぜカットが難しいの？`. Expect `CLIPBOARD_CAUSAL_EVIDENCE` and the line beginning `脆さとカットの難しさ:`. Neither evidence approval nor /sleep is changed.
