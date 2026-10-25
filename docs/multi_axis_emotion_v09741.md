# LLM_CHA v0.9.7.41 — Multi-Axis Emotion Semantic State

Expand v0.9.7.40's scalar affect diagnostic into independent components
with axis, signed value, emotion label, explicit/negation flags, and text
span. Retain the components when an axis has conflicting feelings:
the aggregate for that axis is null, not an apparently neutral zero.

Examples:
- 楽しかったけど疲れた: SADNESS_JOY +0.75, FATIGUE_ENERGY -0.75,
  relation CONTRAST; ACKNOWLEDGE_BOTH.
- 悲しくないし、不安ではない: SADNESS_JOY +0.25,
  ANXIETY_CALM +0.25, relation AND; ACKNOWLEDGE_MULTI_NEGATION.
- 嬉しいけれど悲しい: JOY +0.75 and SADNESS -0.75 both retained,
  aggregate axis null, relation CONTRAST.
- 悲しくない: inferred-neutral +0.25 rather than asserting joy.

The numbers are heuristic design conventions, not emotion
measurements. A user utterance is not evidence of verified inner state.
Expressions outside the narrow recognition grammar can abstain.

## Windows PowerShell
\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.41
python -m unittest -v test_multi_axis_emotion_v09741.py test_continuous_emotion_v09740.py
python evaluate_multi_axis_emotion_v09741.py --output results/multi_axis_emotion_v09741.json
\`\`\`

Implementation is isolated from chat.py, model checkpoints and Semantic
Memory and cannot automatically promote or train data. Existing online
routes retain their previous behavior. Next: evaluate modifier scopes,
contrastive cases, explicit emotions alongside negated feelings, and
cross-axis composition before integrating a controlled opt-in strategy.
