# LLM_CHA v0.2.33.41 — Clarification Policy Evaluation

This branch implements **14 deterministic, hand-authored scenarios** covering ordinary DSS goals, ambiguous references, clarification answers, explicit goal changes, interruption after a pending candidate, cancellation and a generic unknown-token sequence.

Reported measurements: per-turn route agreement, unnecessary-question proxy, needed-clarification recall, new-goal switching rate, accidental candidate approvals and cross-context leakage. Each scenario uses a fresh temporary JSON shadow store.

**Scientific boundaries:** Fixtures are developer-authored, not an independently sampled corpus. High scores only describe these fixtures; no evidence of natural-language generalization or measured real-user inconvenience. The accidental-approval metric counts persisted `approved` records without explicit calls to `confirm`; it is not a classification false-positive rate over all possible approvals. Cross-context leakage is an isolated memory-access probe; the broader product environment is not tested.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.41
git pull origin v0.2.33.41
python -m py_compile clarification_policy_eval_v023341.py
python -m unittest -v test_clarification_policy_eval_v023341.py test_clarification_interruption_v023340.py
python clarification_policy_eval_v023341.py
```

Output: `results/clarification_policy_eval_v023341.json`. Refuses overwrite.

## Next controls

Add genuinely held-out paraphrases and independently labeled ambiguous cases; compare against the v0.2.33.39 no-interruption baseline using identical inputs; distinguish answer correctness, confirm-required count and user turns to resolution; test topic switching without the literal goal keywords. Do not merge to stable runtime or claim native Semantic Memory integration until safety and API compatibility are validated.
