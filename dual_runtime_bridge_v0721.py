"""v0.7.21 opt-in production bridge for Experimental Memory-First.

Only structured Trusted UNKNOWN paths may invoke this bridge. It never
promotes, modifies Trusted weights, or treats Candidate facts as verified.
"""
from dual_semantic_memory_v071 import DualMemory
from experimental_memory_first_v0720 import memory_first

def resolve(question,approved_path,candidate_path,*,enabled,mode="evidence",
            generator=None,resolution="UNKNOWN_KNOWLEDGE"):
    if resolution not in ("UNKNOWN_KNOWLEDGE","GATE_REVIEW") or not enabled:
        return None
    memory=DualMemory(approved_path,candidate_path)
    return memory_first(question,memory,trusted_ask=lambda q:{"status":"UNKNOWN"},
                        experimental_generate=generator,enabled=True,mode=mode)
