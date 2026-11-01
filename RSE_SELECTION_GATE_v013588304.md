# v0.13.58.83.04 — RSE Selection Gate

The previous pilot retrieved these candidates:
- Recent-status question: ID 337, quantified human response (reject); ID 336, human self-report of wellness (reject for AI persona transfer).
- Current-activity question: ID 716, response to enjoyment/hobby rather than current activity (reject).

This update adds a conservative **audit-only** gate. It compares the query and original source question intent, checks current-activity versus enjoyment and quantified-state slots, and flags obvious first-person human-life claims. The checks are heuristic; a missing flag never proves safety. All remaining candidates require manual review and can never be automatically approved.

Windows PowerShell:

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.04-rse-selection-gate
python -m unittest -v test_rse_selection_gate_v013588304.py test_rse_intent_candidates_v013588303.py
python rse_selection_gate_v013588304.py --question "最近どう？" --ids 337 336
python rse_selection_gate_v013588304.py --question "今何してる？" --ids 716
```

The report is saved to results/rse_selection_gate_v013588304.json. Run separately for each query since the default report path is shared. This command does not print source conversations, train, edit the model or alter chat.py.

Next phase: measure false rejects and false accepts against a human-labeled independently held-out selection set; then consider using semantic role matching and assistant-safe paraphrasing. Do not treat token-level lexical evidence or same-intent source retrieval as verified relevance.
