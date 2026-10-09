# LLM_CHA v0.2.31.8 — Evidence-Aware Dialogue Policy

Evidence-aware standalone dialogue-policy experiment. Frozen v0.2.31.5 parser and v0.2.31.7 policy remain available for direct comparison. No new model training, LLM_SEM integration or downstream task execution is claimed.

## What's new
- Distinguish explicit intent cues from an uncertain vector-only candidate.
- Recover some explicit purpose evidence even when the parser returns NEEDS_CONFIRMATION.
- For ambiguity, generate Japanese labels (雑談, 学習, 開発, 問題解決), rather than leaking internal English labels.
- If there are multiple explicit purposes, select PLAN; if casual, select RESPOND; if explicit single goal, select HANDOFF; and if unknown, ask one clarifying question.
- For preference/negation, avoid blindly reintroducing the rejected purpose from surface cues.
- Diagnostic output includes parser state, action, question and evidence source.

## Limitations
Explicit evidence extraction is still regex/lexical and intentionally narrow. It is **not** robust natural-language semantic inference. When parser omits a purpose or misidentifies ordering, the policy may still fail or produce an incorrectly ordered plan. The lexical evidence signals and similarity are not calibrated confidence scores. Question-format tests reject English internal labels but do not establish human-perceived naturalness. A gold standard for nuanced questions needs independent human review.

## Windows commands
```powershell
git fetch origin
git switch v0.2.31.8
git pull origin v0.2.31.8
python -m unittest -v test_evidence_dialogue_policy_v02318.py
python evaluate_evidence_dialogue_policy_v02318.py
python evidence_dialogue_policy_v02318.py
```

## Experiment protocol
- Frozen seen development evaluation: 22 examples from v0.2.31.6.
- Prospective v0.2.31.8 action-focused evaluation: 12 newly authored examples.
- Score new/old action exact matches and structural question-format checks separately.
- Output results/evidence_dialogue_policy_v02318.json.
- Once results are reviewed, the prospective set becomes development evidence, not a pristine holdout.

## Next
Integrate the evidence-aware policy with a persistent DSS, test multiple-turn questions/affirmations/corrections, and evaluate semantic question appropriateness. Compare against an actual LLM_SEM encoder in a separate reproducible experiment.