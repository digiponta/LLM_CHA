# LLM_CHA v0.2.32.0 — Multi-Turn Purpose Generalization Diagnostic

Freeze v0.2.31.9 DSS / v0.2.31.8 policy and test unseen conversational transitions before attaching the language model generator. No generator is wired in this version: evaluation results should determine whether the dialogue policy boundary is ready.

## Evaluation
12 prospective hand-authored dialogues covering confirmation, rejection, goal switches, multiple goals, implicit topic reference, partial confirmation, plan expansion, and repeated clarification. Metrics: action sequence, ordered purpose list, topic, optional relation, history completeness, response/action consistency, and exact whole-scenario success.

These are diagnostic cases and may expose known limitations: the frozen controller handles explicit short 'はい/いいえ' better than free-form confirmations, has no pronoun-resolution mechanism, and may replace rather than extend a plan. This is intentional: failed tests must be reported, not silently changed.

## Windows
```powershell
git fetch origin
git switch v0.2.32.0
git pull origin v0.2.32.0
python -m unittest -v test_multiturn_purpose_v02320.py
python evaluate_multiturn_purpose_v02320.py
```

Output: results/multiturn_purpose_v02320.json

## Generator integration boundary (future v0.2.32.1)
Once the state/error matrix is understood, implement a separate adapter receiving: original user utterance, DSS topic/purposes/relation, policy action, any confirmation question, and the dialogue history. ASK actions should remain deterministic and not call the generator; HANDOFF/RESPOND can call the existing checkpoint; PLAN should realize structured steps without inventing facts. Benchmark source model-only, policy-driven template, and policy-driven generation. Validate topic fidelity, continuity, malformed Japanese and latency. Do not misrepresent a template response as a learned capability.