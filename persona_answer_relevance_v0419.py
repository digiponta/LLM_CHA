"""v0.4.19 read-only answer relevance signals; v0.4.28.1 diagnostics hardening.

Probe cosine similarity can legitimately be negative. Diagnostics must never
change runtime acceptance or throw on invalid numeric probe observations.
"""
from __future__ import annotations
import math
from persona_identity_guard_v0419 import identity_answer

def _valid(value, lower):
    return type(value) in (int,float) and math.isfinite(value) and lower <= value <= 1.0

def diagnose_relevance(question, answer, *, agreement, semantic_agreement):
    if not isinstance(answer,str) or not isinstance(question,str):
        raise ValueError("question and answer required")
    lexical_valid=_valid(agreement,0.0)
    semantic_valid=_valid(semantic_agreement,-1.0)
    identity=identity_answer(question) is not None
    identity_matched=not identity or "長門有希" in answer
    disagreement=lexical_valid and agreement<0.10
    invalid=not (lexical_valid and semantic_valid)
    return {"version":"v0.4.19","identity_question":identity,
            "identity_matched":identity_matched,
            "low_probe_agreement":bool(disagreement),
            "semantic_agreement":semantic_agreement if semantic_valid else None,
            "diagnostic_scores_valid":not invalid,
            "relevance_warning":(identity and not identity_matched) or disagreement or invalid,
            "modifies_truth_gate":False,"writes_memory":False}
