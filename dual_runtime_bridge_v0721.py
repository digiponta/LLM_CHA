"""v0.7.21 opt-in production bridge for Experimental Memory-First.

Only structured Trusted UNKNOWN paths may invoke this bridge. It never
promotes, modifies Trusted weights, or treats Candidate facts as verified.
"""
from dual_semantic_memory_v071 import DualMemory
from experimental_memory_first_v0720 import memory_first
from candidate_reference_approval_v0737 import record_reference
import os

def resolve(question,approved_path,candidate_path,*,enabled,mode="evidence",
            generator=None,resolution="UNKNOWN_KNOWLEDGE"):
    if resolution not in ("UNKNOWN_KNOWLEDGE","GATE_REVIEW") or not enabled:
        return None
    memory=DualMemory(approved_path,candidate_path)
    approved=memory.lookup_approved(question)
    if approved is not None:
        return {"route":"APPROVED_CANDIDATE","answer":approved["answer"],
                "truth_state":"APPROVED","experimental_called":False,
                "auto_promote":False}
    result=memory_first(question,memory,trusted_ask=lambda q:{"status":"UNKNOWN"},
                        experimental_generate=generator,enabled=True,mode=mode)
    if result.get("route")=="EXPERIMENTAL_MEMORY_FIRST":
        threshold=int(os.environ.get("LLM_CHA_AUTO_APPROVE_REFERENCES","10"))
        result["reference_audit"]=record_reference(memory,result["candidate_id"],threshold=threshold)
    return result
