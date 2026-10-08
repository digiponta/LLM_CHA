"""v0.2.7: context-aware rejection and minimal conversational repair.

Only applied to raw generation after existing checks, never to verified retrieval.
"""
from __future__ import annotations
from conversation_diagnostics_v026 import classify_quality

def context_quality_decision(question: str, answer: str, *, enabled: bool = True) -> tuple[bool,str]:
    if not enabled:
        return True,"context quality gate disabled"
    result=classify_quality(question,answer)
    if result["flag"]:
        return False,result["reason"]
    return True,"context quality passed"

def repair_reply(question: str, *, has_context: bool) -> str:
    q=question.strip()
    if not has_context:
        return "どの話についてか、もう少し教えて。"
    if "続けて" in q or "その話" in q:
        return "その話のどの部分を詳しく聞きたい？"
    return "もう少し詳しく教えて。"
