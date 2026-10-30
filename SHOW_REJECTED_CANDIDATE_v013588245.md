# v0.13.58.82.45 — Show rejected candidate text

When an Evidence Gate candidate is rejected, the GUI now shows the original generated answer below its rejection label, clearly marked `［破棄されたLLM回答（不採用・未検証）］`. The separately displayed fallback/reference text remains unchanged.

The text is displayed as diagnostic evidence; it is not automatically accepted, learned, or treated as verified. The negative teacher signal recorded by v0.13.58.82.44 is unchanged.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.45-show-rejected-candidate
python chat_gui.py
```
