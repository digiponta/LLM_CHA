# LLM_CHA v0.2.31.7 — Semantic Dialogue Policy

Implemented as a standalone policy after v0.2.31.5 structured parsing. Parser and vector estimator are unchanged. The policy is deterministic, not learned, and does not execute tasks.

## Action rules
- Missing purpose: ASK_CLARIFICATION
- Structurally ambiguous purpose: ASK_CONFIRMATION
- Multiple purposes: PLAN (retaining parser output order; no invented dependencies)
- Casual purpose: RESPOND
- Single explicit purpose: HANDOFF

The 22 v0.2.31.6 cases are **seen development cases**. A separate prospective 12-case policy fixture is included. Do not claim a final independent benchmark when checking after results become visible.

## Windows commands
```powershell
git fetch origin
git switch v0.2.31.7
git pull origin v0.2.31.7
python -m unittest -v test_semantic_dialogue_policy_v02317.py
python evaluate_semantic_dialogue_policy_v02317.py
python semantic_dialogue_policy_v02317.py
```

Evaluation output: results/semantic_dialogue_policy_v02317.json. Please share the Windows test and evaluation log; policy behavior may be blocked by upstream parser misses. Next improve parser/policy boundaries, confirmation question quality, and integrate DSS in a separate tested version.