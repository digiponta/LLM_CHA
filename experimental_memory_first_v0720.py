"""v0.7.20 Memory-First Experimental runtime (isolated, read-only).

Trusted authority must be consulted first. PENDING candidate evidence is
unverified even when its literal answer matches model generation.
"""
from experimental_semantic_retrieval_v0717 import retrieve
from experimental_rag_v0719 import grounded_prompt

def memory_first(question, memory, *, trusted_ask, experimental_generate=None,
                 enabled=False, mode="evidence"):
    if mode not in {"evidence", "constrained"}:
        raise ValueError("invalid mode")
    trusted=trusted_ask(question)
    if not isinstance(trusted,dict) or trusted.get("status") not in {"ANSWER","UNKNOWN"}:
        raise ValueError("trusted backend must return structured ANSWER/UNKNOWN")
    if trusted["status"]=="ANSWER":
        answer=trusted.get("answer")
        if not isinstance(answer,str) or not answer.strip():
            raise ValueError("empty trusted answer")
        return {"route":"TRUSTED","answer":answer,"truth_state":"APPROVED",
                "experimental_called":False,"auto_promote":False}
    if not enabled:
        return {"route":"TRUSTED_UNKNOWN","answer":None,"truth_state":"UNKNOWN",
                "experimental_called":False,"auto_promote":False}
    hit=retrieve(memory,question)
    if hit["status"]!="MATCH":
        return {"route":"EXPERIMENTAL_UNKNOWN","answer":None,"truth_state":"UNKNOWN",
                "reason":hit["reason"],"experimental_called":False,"auto_promote":False}
    record=hit["record"]
    output={"route":"EXPERIMENTAL_MEMORY_FIRST",
            "answer":"【未承認・候補知識】"+record["answer"],
            "truth_state":"EXPERIMENTAL_UNVERIFIED","candidate_id":record["id"],
            "source_id":record["source_id"],"reason":"candidate_evidence",
            "experimental_called":False,
            "generation_consistent":None,"auto_promote":False}
    if mode=="evidence":
        return output
    if experimental_generate is None:raise ValueError("generator required for constrained mode")
    generated=experimental_generate(grounded_prompt(question,record))
    consistent=isinstance(generated,str) and generated.strip()==record["answer"].strip()
    output["experimental_called"]=True
    output["generation_consistent"]=consistent
    output["generation_status"]="CONSISTENT" if consistent else "REJECTED_TO_EVIDENCE"
    # Never allow a model mismatch to replace the candidate evidence.
    return output
