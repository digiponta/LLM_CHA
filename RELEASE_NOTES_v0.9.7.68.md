# LLM_CHA v0.9.7.68 — Ephemeral Preference Follow-ups

Adds a small session-only `PreferenceDialogue` object, shared by GUI and CLI through `chat.py`.

Scenario:
- `私は、スファレライトが好きです` => `スファレライトが好きなんだね。どんなところが気に入っている？`
- `きれいだから` => `スファレライトがきれいなんだね。`
- Other questions terminate the pending preference follow-up and proceed to the usual attribute and causal evidence paths.

No persistent preference memory, model training, source approval, or /sleep modifications.

Windows check:

```powershell
git fetch origin
git switch v0.9.7.68
git pull --ff-only
python -m unittest -v test_preference_dialogue_v09768.py test_topic_preference_ack_v09767.py test_causal_question_normalization_v09765.py
python chat_window_v061.py
```

The functionality is narrow and rule-based; it does not demonstrate generalized language understanding. Windows runtime tests remain to be run.
