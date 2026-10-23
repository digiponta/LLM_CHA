"""v0.7.37: reference-based automatic Candidate approval.

Count an actual matching Experimental Candidate answer once per resolved request.
A changed question/answer/source resets the streak. Promote only when count > limit.
No Wikipedia/raw-corpus hits count toward Candidate references.
"""
import hashlib
import os
from dual_semantic_memory_v071 import DualMemory,write_store

def version_of(record):
    data="\n".join(record[k] for k in ("question","answer","source_id"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def record_reference(memory, candidate_id, threshold=10):
    if not isinstance(threshold,int) or threshold<1:
        raise ValueError("threshold must be positive")
    candidates=memory.candidates()
    entry=next((r for r in candidates if r["id"]==candidate_id and r["status"]=="PENDING"),None)
    if entry is None:
        return {"status":"NOT_PENDING","reference_count":0,"promoted":False}
    version=version_of(entry)
    previous=entry.get("reference_version")
    count=int(entry.get("reference_count",0)) if previous==version else 0
    count+=1
    entry["reference_version"]=version
    entry["reference_count"]=count
    # Store the reference before promotion so interrupted promotion can be audited.
    write_store(memory.candidate_path,candidates)
    if count<=threshold:
        return {"status":"COUNTED","reference_count":count,"threshold":threshold,
                "promoted":False,"candidate_id":candidate_id}
    try:
        approved=memory.approve(candidate_id)
    except ValueError as exc:
        return {"status":"PROMOTION_BLOCKED","reason":str(exc),
                "reference_count":count,"threshold":threshold,
                "promoted":False,"candidate_id":candidate_id}
    return {"status":"AUTO_APPROVED","reference_count":count,
            "threshold":threshold,"promoted":True,
            "candidate_id":candidate_id,"approved_id":approved["id"]}
