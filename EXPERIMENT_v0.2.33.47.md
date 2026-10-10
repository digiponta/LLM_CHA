# LLM_CHA v0.2.33.47 — Clarification Quality & Goal Resolution

This experiment compares the **unchanged** v0.2.33.40 and v0.2.33.45 context controllers on seven matched, hand-written multi-turn diagnostics. Beyond status matching, it reports correctly completed referent/switch/cancel goals, question-kind relevance, turn cost with penalties for unresolved trajectories, and mean turns conditional on success.

"Question relevance" is an intentionally restricted **slot-type proxy**, not a rating of actual question wording. `confirm(True)` is an explicit test action. Success requires a correctly saved candidate for referent goals; switch/cancel outcomes require their proper route/status and no saved referent.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.47
git pull origin v0.2.33.47
python -m py_compile clarification_goal_quality_v023347.py
python -m unittest -v test_clarification_goal_quality_v023347.py test_multiturn_clarification_efficiency_v023346.py
python clarification_goal_quality_v023347.py
```

Report: `results/clarification_goal_quality_v023347.json` (refuses overwrite).

## Research limitations

These diagnostic scenarios are developer-authored and exposed at design time, hence **not independent**. The older and newer controllers share the same legacy memory adapter; the outcome is not evidence of live Semantic Memory integration. More useful evaluation needs held-out human-labeled questions, freshness/versioning, naturally phrased acknowledgments, explicit false confirmation controls, and cost measured over true user interactions. No stable chat.py or checkpoints are modified.
