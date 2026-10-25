# v0.9.7.44 — Semantic Response Quality Gate (diagnostic sidecar)

A new fail-closed lexical gate checks a frozen Combined-SFT response
against v0.9.7.43 Semantic Response Plan. It rejects obvious polarity
reversal, reasserted negated emotion, absent primary/secondary cues,
and malformed/short output. On failure, an independently written
Semantic-aware reply is used. For unknown inputs, the gate ABSTAINS
rather than pretending to validate arbitrary knowledge responses.

This is a **heuristic diagnostic** and **does not assert semantic
correctness**. Some valid paraphrases will be rejected and some
incorrect statements may pass. Negation token matching is coarse;
complex negation scope requires a future parser. No chat.py route,
model weights, approval policy or Semantic Memory are modified.

## PowerShell

\`\`\`powershell
git fetch origin
git switch --track origin/v0.9.7.44
python -m unittest -v test_semantic_response_gate_v09744.py test_emotion_response_plan_v09743.py
python evaluate_semantic_response_gate_v09744.py \`
  --input results/emotion_response_plan_v09743.json \`
  --output results/semantic_response_gate_v09744.json
\`\`\`

Decision states:
- ACCEPT: lexical indicators met, *not* certified good Japanese.
- FALLBACK: diagnostic contradiction or missing evidence, safe reply used.
- ABSTAIN: unknown/no safe plan, no claim of quality; returned original
  text is **not approved** and must not be interpreted as a gated pass.

Experimental artifacts must not overwrite saved output or automatically
promote Semantic Memory. Review results before any opt-in chat routing.
