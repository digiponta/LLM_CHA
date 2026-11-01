# LLM_CHA v0.13.58.83.20 — Real Chat Transcript / Theme RSE Shadow

This branch adds a **read-only post-session comparator**. It compares answers actually printed by `chat.py` with legacy Unified lookup and Theme RSE. It does not execute `chat.py` itself or infer unobserved answers.

## Local use (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.20-live-transcript-shadow
python -m unittest -v test_rse_live_transcript_v013588320.py test_rse_runtime_theme_comparison_v013588319.py
```
Run your existing `python chat.py` (with your normal model arguments) in a console and ask:
- 閃亜鉛鉱とは
- 少しお話ししませんか？
- 今何してる？

Copy the **actual** lines beginning `You>` and `AI>` and any `[route=...]` markers into `results/chat_actual_v013588320.txt` (UTF-8). You can use Notepad:
```powershell
notepad results/chat_actual_v013588320.txt
```
Then:
```powershell
python compare_rse_live_transcript_v013588320.py --transcript results/chat_actual_v013588320.txt
```

Report is written to `results/rse_live_transcript_shadow_v013588320.json`. Key fields: observed_chat_answer, observed_route_lines, observed_equals_unified, rse_state and classification. **An identical observed response does not prove the route**; rely on explicit route markers when supplied. A mismatch is reported, not masked. If chat.py needs GPU and files, run it using the existing known-good command; this script does not modify any runtime or memory stores.

Warning: `chat.py` may normally write logs or session data; only the comparator is read-only. This is a post-hoc audit, not an automated isolated dry-run. No Theme RSE is enabled in chat.py.
