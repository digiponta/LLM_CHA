# LLM_CHA v0.9.7.34 — Emotion-conditioned Generation Diagnostic

The observed v0.9.7.33 emotion detector/strategy system passed five
manual examples. This branch adds a **read-only A/B generation experiment**
that asks the existing LLM to generate with and without an explicit
emotion/strategy prefix, followed by a conservative lexical contradiction
check. The output is diagnostic; it does NOT replace user-visible
responses or retrain the model.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.34
python -m unittest -v test_emotion_conditioned_generation_v09734.py test_emotion_aware_dialogue_v09733.py
python chat.py
```

At `You>`:

```text
/emotion-compare 今日は楽しかった
/emotion-compare 楽しくなかった
/emotion-compare 悲しくないよ
/emotion-compare 楽しかったけど疲れた
/emotion-compare こんにちは
/emotion-on
今日は楽しかった
/emotion-off
```

Each `/emotion-compare` reports `baseline`, `conditioned`,
`conditioned_gate_pass`, `gate_reason`, and `safe_response`.

**Important limitations:**
- Existing SFT models were NOT trained on `[EMOTION=...]` metadata;
  simply prepending markers is not guaranteed to help and may harm
  generation.
- The gate catches only some obvious lexical contradictions, malformed
  responses and excessive repetition. It cannot prove semantic correctness.
- Even when the gate passes, `selected_response` remains the safe
  deterministic baseline; manual review is required.
- Persona, clipboard safety guards and Semantic Memory remain unchanged.
- Next: evaluate A/B results and train a separate, explicitly
  emotion-conditioned model only if diagnostics justify it.
