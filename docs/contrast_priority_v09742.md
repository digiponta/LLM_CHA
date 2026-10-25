# v0.9.7.42 — Contrast Priority Emotion Semantics

Experimental convention proposed for LLM_CHA: in
「嬉しいけれど悲しい」, けれど gives the emotion in the subsequent
clause higher priority. Preserve both component-level emotions while
exposing SADNESS_LEANING_NEUTRAL, axis SADNESS_JOY=-0.25, with SADNESS
primary and JOY secondary. Reversed order yields +0.25 with JOY primary.

This neutral-offset is a design rule, not measured emotional intensity.

Also:
- 「楽しかったけど疲れた」: FATIGUE is primary, JOY secondary;
  separate axes retained.
- 「悲しくない。むしろ嬉しい。」: explicit JOY +0.75 wins over
  negated SADNESS; do not call this MIXED.
- 「悲しいけれど、どうすればいい？」: without an explicit later
  emotion, refrain from assigning later emotion priority.
- Simple negation and conjunction without a contrast keep existing
  v0.9.7.41 semantics.

The detector does not yet handle quotations, sarcasm, ellipsis,
nested scope, pragmatic counterexamples or full semantic parsing.
This is an isolated diagnostic module, not a live chat integration.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.42
python -m unittest -v test_contrast_priority_v09742.py test_multi_axis_emotion_v09741.py
python evaluate_contrast_priority_v09742.py --output results/contrast_priority_v09742.json
\`\`\`

The output file contains original v0.9.7.41 and new v0.9.7.42 states
for manual comparison. Training, Semantic Memory, chat routing and
checkpoints are unchanged. Review ambiguities before advancing the
model generation stage.
