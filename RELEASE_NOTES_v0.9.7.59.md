# LLM_CHA v0.9.7.59 — Clipboard Attribute Evidence (experimental)

Extends v0.9.7.58-gui. This update adds **read-only source-literal attribute retrieval** in both CLI and GUI because GUI launches the same chat.py.

Supported source fields: chemical composition, Mohs hardness, refractive index, dispersion and principal sources/origins. The extractor reads labeled "key: value" lines rather than hardcoding mineral values, and marks the result EXTERNAL_UNVERIFIED. It returns no answer if no exact label is found or multiple distinct values conflict. Explanatory/causal questions are intentionally not answered by this module.

## Windows verification

```powershell
git fetch origin
git switch v0.9.7.59
git pull --ff-only
python -m unittest -v test_clipboard_attribute_retrieval_v09759.py test_clipboard_evidence_binding_v09757.py test_topic_clipboard_bridge_v09758.py test_gui_clipboard_v09758.py
python chat_window_v061.py
```

Copy the Google result containing these basic data lines, then press クリップボード読込:

- 化学組成: ZnS（硫化亜鉛）
- モース硬度: 3.5 〜 4
- 屈折率: 2.37
- 分散度: ダイヤモンドの約4倍
- 主な産地: スペイン、メキシコ、アメリカ

Test: スファレライトの硬度は → 屈折率は → 主な産地は. Route should be CLIPBOARD_ATTRIBUTE_EVIDENCE. Other existing composition questions should still be answerable.

## Scope and limitations

No neural semantic reasoning is claimed: the new extractor uses labels/regular expressions. It does not validate search results as scientific truth or learn from them. Search result layout changes, unlabeled prose, source attribution and contradictory values may need further work. These changes are committed to GitHub but have not been run on the user's Windows GPU environment.
