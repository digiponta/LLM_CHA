"""v0.7.18 Dual-path Experimental knowledge answer.

Direct Candidate evidence and Adapter generation are distinct. A single
retrieved candidate never confers factual truth or Trusted authority.
"""
from experimental_semantic_retrieval_v0717 import retrieve
from candidate_response_validation_v0713 import candidate_answer_fallback

def answer(memory, question, *, mode="evidence", backend=None, allow=True):
    if mode not in ("evidence","adapter","compare"):
        raise ValueError("mode must be evidence, adapter, or compare")
    if not allow:
        return {"route":"EXPERIMENTAL_DISABLED","answer":None,"truth_state":"UNKNOWN",
                "auto_promote":False}
    hit=retrieve(memory,question)
    if hit["status"]!="MATCH":
        return {"route":"EXPERIMENTAL_UNKNOWN","answer":None,"truth_state":"UNKNOWN",
                "reason":hit["reason"],"auto_promote":False}
    record=hit["record"]
    evidence={"route":"EXPERIMENTAL_MEMORY_EVIDENCE",
              "answer":"【未承認・候補知識】"+record["answer"],
              "truth_state":"EXPERIMENTAL_UNVERIFIED",
              "candidate_id":record["id"],"source_id":record["source_id"],
              "auto_promote":False}
    if mode=="evidence":
        return evidence
    if backend is None:
        raise ValueError("adapter backend required")
    generated=candidate_answer_fallback(record["question"],lambda _:backend(question),record)
    if mode=="adapter":
        return generated
    return {"route":"EXPERIMENTAL_COMPARISON","evidence":evidence,
            "adapter":generated,"truth_state":"EXPERIMENTAL_UNVERIFIED",
            "auto_promote":False}
