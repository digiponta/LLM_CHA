# LLM_CHA v0.9.7.35 — Quality Gate v2 + Real Emotion-conditioned SFT

## Motivation
v0.9.7.34 returned five inappropriate conditioned completions, and the
old superficial gate passed all five. This version applies a **fail-closed,
strategy-whitelist diagnostic gate** to `/emotion-compare`. All five
observed examples become regression tests. Whitelist acceptance is **not**
a general natural language understanding capability; fluent, novel,
correct responses may still be rejected. The selected reply remains
the deterministic baseline even on gate pass.

Unlike v0.9.7.32, the new experimental SFT puts the emotion, dialogue
act and response strategy **into each actual training prompt**:
```text
[EMOTION=ENJOYMENT]
[DIALOGUE_ACT=EMOTION_REPORT]
[RESPONSE_STRATEGY=ACKNOWLEDGE_ENJOYMENT]
人: 今日は楽しかった
AI: <teacher reply>
```

It trains only v0.9.7.32's 73 training examples plus protected QA
replay; 30 holdouts remain evaluation-only. This is a preliminary
supervised conditional-text experiment, not proof of generalization.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.35
python -m unittest -v test_emotion_quality_gate_v09735.py test_emotion_conditioned_generation_v09734.py test_emotion_aware_dialogue_v09733.py
python chat.py
```

At the prompt:
```text
/emotion-compare 今日は楽しかった
/emotion-compare 楽しくなかった
/emotion-compare 悲しくないよ
/emotion-compare 楽しかったけど疲れた
/emotion-compare こんにちは
```
Expect `conditioned_gate_pass=false` on the formerly observed bad outputs
if reproduced; generator outputs may vary with model and seed.

Run dry-run diagnostics:
```powershell
python train_emotion_conditioned_v09735.py `
  --model model/model-llm-try-nagato-chat-v94.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

Opt into separate-checkpoint training:
```powershell
python train_emotion_conditioned_v09735.py `
  --model model/model-llm-try-nagato-chat-v94.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --output model/model-llm-cha-emotion-conditioned-v09735.pt `
  --epochs 3 --lr 0.00002 --replay 3 --train
```

The original checkpoint is never overwritten and an existing output path
causes refusal. The dry-run's unconditioned baseline holdout loss and
after-training conditioned holdout loss use **different input templates**,
so **do not compare them directly**. A later version should add fully
paired conditioned before/after generation, negation/mixed emotion,
blind unseen holdout and protected QA regression.

Caution: training labels are not independently verified and are not the
same labels as those inferred at runtime. Any mismatch must be measured
before deploying this checkpoint to user-visible dialogue.
