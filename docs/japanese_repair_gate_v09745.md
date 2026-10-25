# LLM_CHA v0.9.7.45 — Japanese Repair and Semantic Recheck

Experimental sidecar implements:
1. Check generated text for elementary Japanese fluency red flags.
2. Apply ONLY exact, previously reviewed string substitutions.
3. Re-evaluate the repair through v0.9.7.44 semantic gate.
4. Use a validated semantic fallback if generation is demonstrably bad.
5. REVIEW or ABSTAIN for anything else; neither means safe to publish.

User-directed example:
- Input: 楽しかったけど疲れた
- Original LLM: 疲れたんだね。良かったんでしたね。
- Reviewed correction: お疲れ様でした。楽しかったようで良かったですね。
- Verify both FATIGUE and JOY before selecting it.

This is **not a general Japanese grammar repair engine**. A positive
semantic lexical gate is necessary but not sufficient for fluency.
Unknown/indeterminate responses must not be auto-approved. The
experimental module does not alter chat.py, checkpoints or Semantic
Memory and cannot write training data.

## Windows PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.45
python -m unittest -v test_japanese_repair_gate_v09745.py test_semantic_response_gate_v09744.py
python evaluate_japanese_repair_v09745.py \`
  --input results/emotion_response_plan_v09743.json \`
  --output results/japanese_repair_gate_v09745.json
\`\`\`

Assess generated responses on unseen, independent development cases
before expanding the repair map. Record source, correction and
explicit reviewer decision; do not auto-promote repairs to weights.
