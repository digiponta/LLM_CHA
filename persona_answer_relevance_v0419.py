"""v0.4.19 read-only answer relevance signals for persona dialogue."""
from __future__ import annotations
from persona_identity_guard_v0419 import identity_answer

def diagnose_relevance(question, answer, *, agreement, semantic_agreement):
    if not isinstance(answer,str) or not isinstance(question,str):
        raise ValueError("question and answer required")
    if not 0<=agreement<=1 or not 0<=semantic_agreement<=1:
        raise ValueError("invalid agreement")
    identity=identity_answer(question) is not None
    identity_matched=not identity or "長門有希" in answer
    disagreement=agreement<0.10
    return {"version":"v0.4.19","identity_question":identity,
        "identity_matched":identity_matched,"low_probe_agreement":disagreement,
        "semantic_agreement":semantic_agreement,
        "relevance_warning":(identity and not identity_matched) or disagreement,
        "modifies_truth_gate":False,"writes_memory":False}
