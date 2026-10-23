"""v0.7.38: count stable, source-keyed local evidence references.

One returned source proposition per chat turn counts once. A new evidence
version becomes a new PENDING record; older revisions are not promoted.
Never include Wikipedia text in the candidate fingerprint.
"""
from dual_semantic_memory_v071 import DualMemory,fingerprint
from candidate_reference_approval_v0737 import record_reference

def count_evidence(approved_path,candidate_path,concept,answer,source_id,
                   *,threshold=10,route="RAW_CONCEPT_EVIDENCE"):
    if route not in ("RAW_CONCEPT_EVIDENCE","CORPUS_MEMORY"):
        raise ValueError("unsupported reference route")
    if not all(isinstance(x,str) and x.strip() for x in (concept,answer,source_id)):
        return {"status":"INVALID_EVIDENCE","promoted":False}
    if len(answer)>12000:
        return {"status":"OVERSIZE","promoted":False}
    memory=DualMemory(approved_path,candidate_path)
    question="原文証拠："+concept.strip()+" #"+__import__("hashlib").sha256((source_id.strip()+"#"+route).encode("utf-8")).hexdigest()[:12]
    # Stable identity includes source, so an identical answer from a
    # different corpus is not automatically treated as the same evidence.
    marker=source_id.strip()+"#"+route
    existing=next((r for r in memory.candidates()
                   if r["question"]==question and r["source_id"]==marker
                   and r["answer"]==answer.strip() and r["status"]=="PENDING"),None)
    if existing is None:
        approved=next((r for r in memory.approved()
                       if r["question"]==question and r["source_id"]==marker
                       and r["answer"]==answer.strip()),None)
        if approved is not None:
            return {"status":"ALREADY_APPROVED","promoted":False,"reference_count":None}
        candidate_id=memory.propose(question,answer.strip(),marker)
    else:
        candidate_id=existing["id"]
    result=record_reference(memory,candidate_id,threshold=threshold)
    result["route"]=route
    return result
