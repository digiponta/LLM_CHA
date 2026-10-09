# LLM_CHA v0.2.31.9 — Evidence-Aware Dialogue State Integration

A standalone, deterministic multi-turn prototype. Integrates v0.2.31.8 Evidence-Aware Policy with persistent DSS. No language model retraining or downstream execution.

## Features
- Preserve topic, ordered purposes, relation, pending confirmation, rejection history and conversation history.
- Resolve short affirmative/negative answers to a pending confirmation.
- Reset the previous goal on explicit topic/goal changes.
- Hold multi-purpose plans in declared order rather than executing them.
- Avoid exact repetition of the immediately preceding question.
- Keep the distinction between task HANDOFF, PLAN, and conversational RESPOND.

## Windows
```powershell
git fetch origin
git switch v0.2.31.9
git pull origin v0.2.31.9
python -m unittest -v test_evidence_dialogue_state_v02319.py
python evidence_dialogue_state_v02319.py
```

Suggested scenarios:
- Pythonに興味がある → はい → /state
- /reset → Pythonに興味がある → いいえ → Pythonを勉強したい
- /reset → LLMを勉強してから開発したい → /state
- やっぱり画像認識を開発したい → /state

## Limits
Purpose inference and evidence remain rule-based or lexical; confidences are not calibrated. No actual task execution. Confirmation questions can be semantically awkward if a vector candidate is unsuitable. Exact repetition suppression is not a full semantic question-quality gate. The v0.2.31.8 action evaluation is not a multi-turn benchmark. Next create a prospective multi-turn test with refusal, changing intent, pronouns, repeated clarification and purpose retention, and compare DSS baseline vs integrated controller.
