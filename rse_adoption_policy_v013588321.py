"""Conservative RSE adoption policy, shadow only. Not wired into chat.py.

Priority: existing accepted semantic route > approved and relation-matched
RSE answer > UNLEARNED for evaluated uncovered cases.
A mere model KNOWN gate is not evidence of question-answer relevance.
"""
from __future__ import annotations

from dataclasses import dataclass,asdict

PROTECTED_ROUTES={"MEMORY_ATOMIC_EXACT","TYPED","CANONICAL","UNIFIED","MEMORY_APPROVED_EXACT"}
UNKNOWN="未学習です"

@dataclass(frozen=True)
class Decision:
    action:str
    answer:str|None
    reason:str
    source:str

def decide(*,observed_answer:str|None,observed_route:str,
           rse_status:str,rse_answer:str|None,
           rse_approved:bool=False,
           shadow_only:bool=True)->Decision:
    """Policy evaluates explicit evidence; never treats a synthetic candidate as approved."""
    route=(observed_route or "").strip().upper()
    if route in PROTECTED_ROUTES and observed_answer and observed_answer!=UNKNOWN:
        return Decision("PRESERVE_EXISTING",observed_answer,"PROTECTED_KNOWLEDGE_ROUTE","EXISTING_RUNTIME")
    if rse_status=="ANSWER_SELECTED" and rse_answer and rse_approved:
        return Decision("SELECT_RSE",rse_answer,"REVIEWED_THEME_INTENT_RELATION_MATCH","APPROVED_RSE")
    if rse_status=="ANSWER_SELECTED":
        return Decision("REVIEW_REQUIRED",None,"CANDIDATE_NOT_APPROVED","RSE_SHADOW")
    if rse_status in {"UNLEARNED","MEMORY_NOT_FOUND"}:
        return Decision("ABSTAIN",UNKNOWN,"NO_APPROVED_SUITABLE_ANSWER","POLICY")
    if rse_status in {"MEMORY_PRESENT_UNVERIFIED","MEMORY_TRUTH_RESTRICTED","MEMORY_AMBIGUOUS"}:
        return Decision("REVIEW_REQUIRED",None,"MEMORY_STATE_REQUIRES_EXISTING_TRUST_POLICY","MEMORY_SHADOW")
    return Decision("REVIEW_REQUIRED",None,"INSUFFICIENT_POLICY_EVIDENCE","POLICY")

def evaluate_transcript_comparison(report:dict)->dict:
    output=[]
    for case in report.get("cases",[]):
        observed=case.get("observed_chat_answer")
        routes=case.get("observed_route_lines") or []
        route=""
        for line in routes:
            if line.startswith("[route="):
                route=line.split("[route=",1)[1].split("]",1)[0]
                break
        # RSE candidate is a shadow candidate and is NOT inherently approved.
        d=decide(observed_answer=observed,observed_route=route,
                 rse_status=case.get("rse_state",""),
                 rse_answer=case.get("rse_answer"),rse_approved=False)
        output.append({"query":case.get("query"),"observed_route":route or "UNKNOWN",
                       "observed_answer":observed,"rse_state":case.get("rse_state"),
                       **asdict(d)})
    return {"status":"SHADOW_ADOPTION_POLICY","cases":output,
            "live_integration":False,"source_data_modified":False}
