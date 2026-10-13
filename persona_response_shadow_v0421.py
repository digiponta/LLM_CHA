"""v0.4.21 read-only shadow evaluation; not a response acceptance policy.

Diagnostics are interpretable heuristics, not measured correctness estimates.
"""
from __future__ import annotations
import re
from persona_dialogue_intent_v0420 import classify_dialogue_intent
from persona_answer_relevance_v0419 import diagnose_relevance

def evaluate(question, answer, *, agreement, semantic_agreement, accepted):
    if not isinstance(accepted,bool):
        raise ValueError("accepted must be boolean")
    relevance=diagnose_relevance(question,answer,agreement=agreement,
                                semantic_agreement=semantic_agreement)
    intent=classify_dialogue_intent(question)["intent"]
    normalized=answer.strip()
    abstention=(not normalized or normalized in {"未学習です","(no response)"})
    fragments=bool(re.search(r"[|｜]|読切・",normalized))
    divergent=(relevance["diagnostic_scores_valid"] and agreement<0.35 and semantic_agreement>=0.82)
    identity_mismatch=relevance["identity_question"] and not relevance["identity_matched"]
    flags=[]
    if not relevance["diagnostic_scores_valid"]:flags.append("INVALID_DIAGNOSTIC_SCORE")
    if divergent:flags.append("AGREEMENT_DIVERGENCE")
    if fragments:flags.append("OUTPUT_FRAGMENT_MARKERS")
    if identity_mismatch:flags.append("IDENTITY_MISMATCH")
    if abstention:flags.append("ABSTENTION")
    if not normalized:flags.append("EMPTY_ANSWER")
    return {"version":"v0.4.21","mode":"SHADOW_ONLY","intent":intent,
            "flags":flags,"needs_review":bool(flags),
            "accepted_by_runtime":accepted,
            "agreement":agreement,"semantic_agreement":semantic_agreement,
            "decision_unchanged":True,"truth_gate_modified":False,
            "semantic_memory_writes":0,"training_enabled":False}
