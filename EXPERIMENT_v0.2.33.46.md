# LLM_CHA v0.2.33.46 — Multi-Turn Clarification Efficiency

This experiment compares the unchanged v0.2.33.40 and v0.2.33.45 dialogue policies on ten hand-authored multi-turn scenarios with identical inputs and separate temporary shadow memory stores.

Scenarios include canonical and polite clarification, user approval or rejection, repeat reference lookup, explicit/indirect interruption, ambiguity then resolution, cancellation, candidate interruption, and isolation of conversation B.

Measured outcomes:
- Exact per-turn **status** match and full-trajectory success;
- Question events, counting both `clarify` statuses, `confirm` prompts, and actual DSS `ASK_CLARIFICATION`/`ASK_CONFIRMATION` actions;
- First resolution turn in successful or failed trajectories (use only with outcome quality);
- Unexpected approved values in context A, plus explicit approval requirement;
- Per-case trace for manual inspection.

All ten trajectories are **researcher-created development diagnostics**, not independently annotated natural Japanese conversation. A higher score does not establish language understanding or user-convenience improvements in real-world use. Question event counts are **not** the number of user utterances; some statuses require another user's reply.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.46
git pull origin v0.2.33.46
python -m py_compile multiturn_clarification_efficiency_v023346.py
python -m unittest -v test_multiturn_clarification_efficiency_v023346.py test_context_aware_clarification_v023345.py
python multiturn_clarification_efficiency_v023346.py
```

Produces `results/multiturn_clarification_efficiency_v023346.json` (refuses overwrite).

## Next

Review per-turn failures, create a genuinely unobserved set of full trajectories labeled by a different annotator, distinguish resolving intent from merely reaching `resolved`, and evaluate actual question text for relevance. The purpose DSS is project code; reference ambiguity remains rule-based. Production Semantic Memory, stable chat runtime, language generation and /sleep are **not** integrated.
