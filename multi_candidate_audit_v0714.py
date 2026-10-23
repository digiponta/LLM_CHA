"""v0.7.14 multi-candidate routing audit, without granting trust.

All probes use a supplied backend (a real adapter or deterministic test double).
Candidate answer matches demonstrate consistency, not external factual truth.
"""
from candidate_aware_fallback_v0712 import candidate_match
from candidate_response_validation_v0713 import candidate_answer_fallback

def route_probe(question, memory, backend, *, trusted_answer=None, enabled=True):
    if trusted_answer is not None:
        return {"route":"TRUSTED","answer":trusted_answer,"truth_state":"APPROVED",
                "experimental_called":False,"auto_promote":False}
    if not enabled:
        return {"route":"TRUSTED_UNKNOWN","answer":None,"truth_state":"UNKNOWN",
                "experimental_called":False,"auto_promote":False}
    record=candidate_match(memory,question)
    if record is None:
        return {"route":"NO_CANDIDATE","answer":None,"truth_state":"UNKNOWN",
                "experimental_called":False,"auto_promote":False}
    result=candidate_answer_fallback(question,backend,record)
    return dict(result,experimental_called=True)

def evaluate_probes(memory, backend, *, known_questions=(), unknown_questions=()):
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    approved=memory.approved()
    rows=[]
    for r in pending:
        q=r["question"]
        result=route_probe(q,memory,backend)
        rows.append({"kind":"candidate","question":q,"candidate_id":r["id"],
                     "route":result["route"],"truth_state":result["truth_state"],
                     "experimental_called":result["experimental_called"],
                     "exact_match":result.get("reason")=="candidate_exact_consistency"})
    for r in approved:
        q=r["question"]
        result=route_probe(q,memory,backend,trusted_answer=r["answer"])
        rows.append({"kind":"approved","question":q,"candidate_id":None,
                     "route":result["route"],"truth_state":result["truth_state"],
                     "experimental_called":result["experimental_called"],"exact_match":None})
    for q in unknown_questions:
        if candidate_match(memory,q) is not None or memory.lookup_approved(q) is not None:
            raise ValueError("unknown probe overlaps with stored knowledge")
        result=route_probe(q,memory,backend)
        rows.append({"kind":"unknown","question":q,"candidate_id":None,
                     "route":result["route"],"truth_state":result["truth_state"],
                     "experimental_called":result["experimental_called"],"exact_match":None})
    protected=[r for r in rows if r["kind"]=="approved"]
    unknown=[r for r in rows if r["kind"]=="unknown"]
    candidate=[r for r in rows if r["kind"]=="candidate"]
    return {"version":"v0.7.14","cases":rows,
      "candidate_count":len(candidate),
      "candidate_exact":sum(bool(r["exact_match"]) for r in candidate),
      "candidate_exact_rate":sum(bool(r["exact_match"]) for r in candidate)/len(candidate) if candidate else None,
      "protected_count":len(protected),
      "trusted_protected_preserved":all(r["route"]=="TRUSTED" and not r["experimental_called"] for r in protected),
      "unknown_count":len(unknown),
      "unknown_rejected":sum(r["route"]=="NO_CANDIDATE" for r in unknown),
      "auto_promote":False,"factual_verification":"NOT_PERFORMED"}
