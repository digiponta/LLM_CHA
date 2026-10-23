# LLM_CHA v0.7.44.14 — Opt-in Alias Lookup Integration

The 6/6 PASS v0.7.44.13 topic normalization test was followed by a
narrow runtime integration for the literal query:
`量子重ね合わせについて教えて` → `重ね合わせについて教えて`.

When `LLM_CHA_TOPIC_NORMALIZE=1`, the existing Wikipedia fallback is
invoked with the normalized target after truth-gate checks. Successful
responses use `route=TOPIC_ALIAS_WIKIPEDIA`, maintain
`EXTERNAL_UNVERIFIED`, and are neither trained nor promoted.

The original user utterance is preserved; this prevents accidental
rewriting of Candidate capture, command execution, or source attribution.
The GUI launcher enables the flag. The CLI defaults to disabled.

```powershell
git pull
python -m unittest -v test_topic_recovery_v074413.py test_topic_normalization_runtime_v074414.py
$env:LLM_CHA_TOPIC_NORMALIZE="1"
python chat.py
Remove-Item Env:LLM_CHA_TOPIC_NORMALIZE
python chat_gui_v07447.py
```

Try `量子ビットとは？`, `量子重ね合わせについて教えて`,
`重ね合わせについて教えて`, `もっと詳しく` and
`宇宙とは`, `もう少し詳しく`. Only the explicit alias case
is newly handled. Evidence-aware follow-up in the main runtime is
**not yet integrated** and needs additional source and cursor checks
before enabling. Regression/GPU acceptance is pending.
