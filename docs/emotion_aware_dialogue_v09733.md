# LLM_CHA v0.9.7.33 — Emotion-aware Semantic Dialogue v0.1

This branch implements an **opt-in**, deterministic emotion/intent
detector and response-strategy selector. It is an interpretable
reference baseline, **not** a trained emotion classifier, not
emotion-conditioned LLM generation and not proof of empathic understanding.

## Pipeline

User text → dialogue-act guard → conservative emotion cue detection →
negation / explicit contrast handling → strategy selection → short response.

Emotions: JOY, ENJOYMENT, ANGER, SADNESS, DISAPPOINTMENT, FATIGUE,
GRATITUDE, UNCERTAINTY; also NON_SADNESS, MIXED and GREETING.
Unrecognized text and questions abstain, falling through to normal
generation. Product-grounded clipboard answers retain higher priority.
Commands are not handled as emotion utterances. The latest detection is
ephemeral: train_ready=False, auto_promote=False, persisted=False.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.33
python -m unittest -v test_emotion_aware_dialogue_v09733.py
python chat.py
```

Try:
```text
/emotion-on
今日は楽しかった
こんにちは
楽しくなかった
悲しくないよ
楽しかったけど疲れた
/emotion-status
/emotion-off
```

Expect separate EMOTION_AWARE_STRATEGY routes, while disabled mode uses
the existing runtime. This experiment does not change LLM parameters
and must not be interpreted as a semantic SFT result.

## Known limitations

- Lexical rules cover only explicit expressions; vague metaphors,
  sarcasm, negation outside enumerated phrases and difficult scope
  constructs may fail or be misclassified.
- A mixed response is generic; no true compositional LLM generation yet.
- Detecting an expressed emotion is not evidence of the user's actual
  psychological state.
- The detector is not always correct and should abstain when uncertain.
- Next stage: blind labeled evaluation and controlled conditional SFT,
  with semantic tags actually included in model inputs.
