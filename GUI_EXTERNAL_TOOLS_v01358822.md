# LLM_CHA v0.13.58.82.2 — GUI external tools restoration

Restores buttons that were missing in the v0.13.58.82 GUI refresh:

- **ググる**: open Google search in user's external browser, using current input text or a prompt.
- **クリップ読込**: read up to 4,000 characters of plain text from clipboard into a temporary GUI preview in the diagnostic tab; label it unverified. Does **not** automatically insert this into LLM context or model training.
- **Wiki検索**: query Japanese Wikipedia public MediaWiki API for up to 3 short article extracts in a nonblocking thread, display results in diagnostic tab as *external unverified* information. Network access required.

The prior legacy GUI may have had more deeply integrated flows. This is a safe GUI restoration of the **controls**, not a claim of full preservation of prior clipboard-to-context integration. It does not alter the LLM answer, Wikipedia approval, or /sleep behavior. The current CLI still uses the existing model and command handler.

PowerShell:
```powershell
git fetch origin
git switch v0.13.58.82.2-gui-web-clipboard-wiki
python -m unittest -v test_chat_gui_external_tools_v01358822.py test_chat_gui_utf8_v01358821.py
python chat_gui.py
```
