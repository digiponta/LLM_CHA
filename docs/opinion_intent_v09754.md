# v0.9.7.54 — OPINION Intent (Nagato persona)

Short declarative value judgments are detected before unknown-knowledge resolution when `--final-guard` is enabled.

- `満足は大切`, `健康は重要`, `運動は必要` → `そう。`
- `満足は大切ではない` → `そう。` (acknowledgment, not agreement)
- `満足とは` → existing definition/search priority
- `満足は` → existing incomplete-utterance response
- Questions, compound text and unsupported factual propositions → existing processing.

OPINION is `USER_OPINION_UNVERIFIED`. It is not a fact, not promoted, not trained and not persisted.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.54
python -m unittest -v test_opinion_intent_v09754.py test_incomplete_utterance_v09753.py test_definition_intent_v09752.py test_conversational_intent_v09751.py
python chat_window_v061.py --final-guard --gui-only-input
```

Expected 38 tests (10+9+9+10). Runtime integration and actual GUI behavior must be verified on Windows.