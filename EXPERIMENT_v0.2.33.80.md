# LLM_CHA v0.2.33.80 — Speech-Act & Reference Safety

The v0.2.33.79 GPU trace showed:
- `ありがとう` -> `未学習です` (speech-act mismatch)
- `あの実験の続き` -> unrelated LLM output (reference accepted without a target)
- `もう少し詳しく` -> `未学習です` (follow-up target not resolved)

This version introduces conservative *pre-generation* handling in `chat.py` for exact forms of acknowledgement, ambiguous experiment reference, and underspecified follow-up. Acknowledgements receive `どういたしまして。`. Ambiguous references request the experiment/topic. Follow-ups request a concrete target instead of assuming that UNVERIFIED content may be generated. Nonmatching queries, slash commands and existing Truth Gate behavior are unchanged.

**Limitation**: this is a safety-first clarification policy, **not** full context persistence. It does not learn to resolve the previous topic, change model weights or promote any evidence. The initial user-facing response is deterministic; persona-specific language is not yet tailored.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.80
git pull origin v0.2.33.80
python -m py_compile chat.py speech_act_reference_v023380.py
python -m unittest -v test_speech_act_reference_v023380.py test_extended_chat_runtime_v023378.py
python extended_chat_runtime_v023378.py --run --timeout 240
python conversation_generalization_v023379.py --run --timeout 240
```

Check `results/conversation_generalization_v023379.json` for `thanks`, `reference_ambiguity`, and `topic_followup` answers. For the latter, expected behavior is an explicit request for the target, **not** knowledge recall.
