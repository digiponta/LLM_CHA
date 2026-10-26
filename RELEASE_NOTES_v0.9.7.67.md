# LLM_CHA v0.9.7.67 — Topic-aware preference acknowledgement

Observed regression: after successful clipboard causal and attribute evidence responses, `私は、スファレライトが好きです` unexpectedly generated `読書。静かな状態。`.

This experimental release adds `topic_preference_ack_v09767.py` to recognize explicit Japanese positive preference statements and respond with a short, on-topic conversational acknowledgement. `chat.py` routes these utterances before generic model generation, without changing the established evidence retrieval paths. No preferences are promoted, persisted, or learned automatically.

Windows:
```powershell
git fetch origin
git switch v0.9.7.67
git pull --ff-only
python -m unittest -v test_topic_preference_ack_v09767.py test_causal_question_normalization_v09765.py test_release_diagnostics_v09766.py
python chat_window_v061.py
```

Test `私は、スファレライトが好きです` after searching and copying a sphalerite page; expected route `TOPIC_PREFERENCE_ACK`. Also repeat `なぜカットが難しいの？` and `屈折率は？` to check for evidence retrieval regression. This is a narrow rule-based conversational safeguard, not a general persona fix. The previously planned checkpoint-inspection work remains pending.

Local Windows execution has not yet been validated.
