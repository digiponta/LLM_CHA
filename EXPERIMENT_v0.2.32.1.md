# LLM_CHA v0.2.32.1 — Contextual Purpose Resolution & Incremental Composition

## Scope
This branch adds a conservative adapter over the frozen v0.2.31.9 dialogue controller:
- Resolve demonstratives such as 「それ」 against a known DSS topic, only when an existing topic is available.
- REPLACE a prior goal for an unambiguous new goal (「それを作ってみたい」).
- ADD a new goal for additive utterances (「それから開発もしたい」), preserving the previous goal order and explicit sequential relation.
- Keep explicit goal switches, confirmation, negative replies and ordinary conversation on the baseline path.
- Export generation_context() with topic, purposes, relation, action and conversation history for subsequent model integration.

This is a deliberately constrained lexical/discourse prototype. It does not solve general coreference or Japanese compositional semantics, and HANDOFF/PLAN are still not executed by the LLM generator.

## Evaluation
Previously inspected v0.2.32.0 12-dialogue dataset is now a seen development diagnostic. A separate six-dialogue prospective dataset covers references, additive plans, explicit switching, confirmation, and unknown requests. Score full sequences and each field; preserve observed failures.

## Windows
```powershell
git fetch origin
git switch v0.2.32.1
git pull origin v0.2.32.1
python -m unittest -v test_contextual_purpose_v02321.py
python evaluate_contextual_purpose_v02321.py
python contextual_purpose_composition_v02321.py
```

Suggested interactions:
1. Pythonを勉強したい → それを作ってみたい → /state
2. /reset → LLMを勉強したい → それから開発もしたい → /state
3. /reset → Pythonに興味がある → いいえ → Pythonを勉強したい

## Next step: LLM_CHA generator integration
Use generation_context() as a contract for a separate version. Compare baseline raw checkpoint output, deterministic DSS responses, and DSS-conditioned checkpoint output. ASK actions remain controller-generated. Evaluate topical relevance, purpose fidelity, hallucination, Japanese fluency, and latency. Do not claim that a template or policy decision is produced by a learned model.

## Limitations
Explicit markers can be ambiguous in other contexts; a pronoun without grounded topic does not resolve. Additive goals in negated or alternative clauses need more sophisticated scope handling. Relation checks in earlier v0.2.32.0 tests do not establish broad relation retention. Reserve another clean test set after inspecting the present results.
