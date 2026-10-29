# v0.13.58.82.4 — Temporary Evidence prototype

The GUI now keeps a **session-only**, in-memory topic and up to five unverified clipboard/Wikipedia snippets. When the user searches for a topic, the GUI remembers it. Clipboard content is attached to that topic; Wikipedia snippets are attached with the search topic. For the specific demonstrated sphalerite composition query, the GUI can answer using an explicit `ZnS（硫化亜鉛）` match and display the unverified source label.

Limitations: This is a narrow **deterministic prototype**, NOT general retrieval-augmented generation. Other questions still follow existing chat.py. Wikipedia's description without an explicit ZnS formula is not by itself enough for the current extraction rule. Google opens a browser; it does not scrape the page. Clipboard text is untrusted and should not be used to override commands or model policy. No evidence is saved to Semantic Memory or trained into weights. CLI remains the v0.13.58.82.3 route without this GUI-only evidence binding.

PowerShell:
```powershell
git fetch origin
git switch v0.13.58.82.4-temporary-evidence
python -m unittest -v test_temporary_evidence_v01358824.py test_natural_tool_router_v01358823.py
python chat_gui.py
```

Manual regression: 「スファレライトをぐぐって」 -> copy a source containing 「化学組成：ZnS（硫化亜鉛）」 -> 「クリップボードを読み込んで」 -> 「化学組成は？」. Expect a temporary externally-unverified answer. A fresh session, wrong topic, or absence of the ZnS statement must not produce the answer.
