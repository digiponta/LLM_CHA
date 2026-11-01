# v0.13.58.83.05 — Integrated RSE / Safe Fallback

Combines the existing intent router, RealPersonaChat response shortlist, and selection gate into an audit-only command. Retrieved source-speaker replies are **never** returned directly as AI responses. In dialogue-intent cases, the output is a conservative assistant-authored fallback proposal, regardless of shortlist content. This is a deliberate baseline, not yet RSE expansion or validated naturalness. Factual prompts defer to existing Semantic Memory.

Windows PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.05-rse-fallback-integration
python -m unittest -v test_rse_integrated_v013588305.py test_rse_selection_gate_v013588304.py
python rse_integrated_v013588305.py --question "最近どう？" --report results/rse_status_v013588305.json
python rse_integrated_v013588305.py --question "今何してる？" --report results/rse_activity_v013588305.json
python rse_integrated_v013588305.py --question "少し話さない？" --report results/rse_invitation_v013588305.json
python rse_integrated_v013588305.py --question "スファレライトとは？" --report results/rse_factual_v013588305.json
```

Interpretation: SAFE_FALLBACK_PROPOSED means a *diagnostic suggestion*, not a live chat response. Candidate reason flags are heuristic. An unflagged source reply is MANUAL_REVIEW_REQUIRED, never automatically approved. The source dataset has 2,286 CP pairs from the pilot. Neither the model checkpoint nor chat.py is changed. Next: independent positive/negative human-labeled cases to estimate erroneous rejection, and then explicitly bounded, non-autobiographical contextual expansion.
