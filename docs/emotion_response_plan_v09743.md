# LLM_CHA v0.9.7.43 — Semantic Response Plan

Converts v0.9.7.42 priority states into a response plan without
discarding constituent emotions. In particular:
- 「嬉しいけれど悲しい」 -> primary SADNESS -0.75; overall
  SADNESS_JOY -0.25; secondary JOY.
- 「悲しいけれど嬉しい」 -> primary JOY +0.75; overall +0.25;
  secondary SADNESS.
- 「嬉しいけれど悲しいけれど嬉しい」 -> primary JOY;
  secondary SADNESS only (deduplicated), while raw components
  remain available in the upstream state.
- 「楽しかったけど疲れた」 -> primary FATIGUE,
  secondary JOY and both axes preserved by upstream detector.
- 「悲しくない。むしろ嬉しい。」 -> explicit JOY, not MIXED.

Separate primary component intensity from overall contrast-adjusted
neutral magnitude. Both are heuristic conventions, not measured emotions.

## Run on Windows PowerShell
\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.43
python -m unittest -v test_emotion_response_plan_v09743.py test_contrast_priority_v09742.py
python evaluate_emotion_response_plan_v09743.py \`
  --checkpoint model/model-llm-cha-factorial-v09738-both.pt \`
  --tokenizer model/tokenizer-v0.7-bpe.json \`
  --output results/emotion_response_plan_v09743.json
\`\`\`

This comparison is **qualitative only**. The v0.9.7.38 Combined SFT
was not trained on v0.9.7.43's new strategy/primary-emotion tags.
Do not infer that the plan is better on unseen prompts. No runtime
routing, model training, Semantic Memory writes, or automatic promotion
is introduced.
