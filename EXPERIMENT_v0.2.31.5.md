# LLM_CHA v0.2.31.5 — Structured Semantic Purpose Estimation

Experimental hybrid prototype (not a trained semantic parser).
Purpose classes and character N-gram vector similarity from v0.2.31.4 are augmented by **explicit structural cues**. The parser separates topic, multiple purposes, relation, polarity, status and evidence; the vector candidate is treated as a hint, not unqualified certainty.

## Actions
READY → HANDOFF; NEEDS_PLANNING → PLAN; NEEDS_CONFIRMATION → ASK_CONFIRMATION; NEEDS_CLARIFICATION → ASK_CLARIFICATION. No LLM generation or DSS integration is claimed.

## Windows commands
```powershell
git fetch origin
git switch v0.2.31.5
git pull origin v0.2.31.5
python -m unittest -v test_structured_semantic_purpose_v02315.py
python structured_semantic_purpose_v02315.py
```

Suggested probes:
- LLMを勉強してから開発したい
- Pythonは開発じゃなく勉強したい
- Pythonに興味がある
- Pythonでアプリを開発したい

## Important limits
Rules for purpose cues and relations are hand-authored. They should not be called semantic generalization. The confidence attribute is uncalibrated N-gram similarity. The prototype is an independent interpretation stage, not a full multi-turn dialogue runtime. Next: construct labeled structural evaluation (including unseen paraphrases, conjunctions, negation, ambiguous utterances); report exact structure metrics, not just category accuracy. Afterwards compare with a genuinely learned LLM_SEM encoder if accessible.