"""v0.7.39: separate operational approval from factual truth on source evidence."""
from dual_semantic_memory_v071 import DualMemory

def evidence_state(approved_path,candidate_path,concept,answer,source_id,route):
    import hashlib
    if route not in ("CORPUS_MEMORY","RAW_CONCEPT_EVIDENCE"):
        raise ValueError("unsupported route")
    question="原文証拠："+concept.strip()+" #"+hashlib.sha256((source_id.strip()+"#"+route).encode("utf-8")).hexdigest()[:12]
    marker=source_id.strip()+"#"+route
    mem=DualMemory(approved_path,candidate_path)
    matches=lambda r:r["question"]==question and r["answer"]==answer.strip() and r["source_id"]==marker
    if any(matches(r) for r in mem.approved()):
        return {"approval_state":"APPROVED","truth_state":"UNVERIFIED"}
    pending=next((r for r in mem.candidates() if matches(r) and r["status"]=="PENDING"),None)
    return {"approval_state":"PENDING" if pending else "NOT_REGISTERED",
            "reference_count":pending.get("reference_count",0) if pending else 0,
            "truth_state":"UNVERIFIED"}
