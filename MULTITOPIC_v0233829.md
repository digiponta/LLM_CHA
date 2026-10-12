# LLM_CHA v0.2.33.82.9 — Mixed-State Component End-to-End Validation

This phase adds a deterministic **fixture-only** end-to-end evaluation path
through the *real* conversation topic adapter, proposition cursor, and
read-only proposition Truth Overlay classes. It does not start GPU chat or
use production Semantic Memory files.

## Test states

The fixture has five explicit proposition states:

| Proposition | State | Expected |
| --- | --- | --- |
| A | TRUE | display |
| B | FALSE | skip |
| C | UNVERIFIED | display with unverified state |
| D | OUTDATED | skip |
| E | CONTESTED | skip |

Also checks all eligible content exhausted, resets, topic switching,
subject-level blocking, stable proposition IDs, and read-only overlay.

## Regressions

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git pull origin v0.2.33.82-multitopic-context
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py test_proposition_truth_v0233827.py test_truth_integration_v0233827.py test_proposition_review_v0233828.py test_mixed_state_e2e_v0233829.py
```

Expected: **90 tests** (82 previous + 8 new), not yet verified on local machine.

## Important limit

The new evaluator is **not a live chat.py / GPU evaluation**. It reuses
production components but supplies isolated corpus and Truth State fixtures.
Live chat evaluation with a fixture-injection mechanism remains a separate
acceptance stage. Do not claim GPU mixed-state acceptance based on this suite.

For actual chat.py test, first prepare a distinct fixture-specific
corpus path and Truth Overlay path, not the ordinary user data files. Run
against cloned test data and verify rollback afterward. Until isolation
is implemented and assessed, avoid changing production Truth State simply to
obtain mixed-state GPU test output.
