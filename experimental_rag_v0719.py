"""v0.7.19 Experimental retrieval-augmented generation (isolated).

Selected PENDING answer is used as an explicit prompt context. Generation is
accepted only on exact evidence consistency; no factual verification is implied.
"""
from experimental_semantic_retrieval_v0717 import retrieve

def grounded_prompt(question,record):
    return ("参照情報（未承認）: "+record["question"]+" => "+record["answer"]+
            "\nこの参照情報だけを使い、質問に短く答えてください。\n質問: "+question)

def run_question(memory,question,backend,*,enabled=True):
    if not enabled:return {"route":"EXPERIMENTAL_DISABLED","truth_state":"UNKNOWN","answer":None,"auto_promote":False}
    hit=retrieve(memory,question)
    if hit["status"]!="MATCH":
        return {"route":"EXPERIMENTAL_UNKNOWN","truth_state":"UNKNOWN","answer":None,
                "reason":hit["reason"],"auto_promote":False}
    r=hit["record"]
    generation=backend(grounded_prompt(question,r))
    exact=str(generation or "").strip()==r["answer"].strip()
    return {"route":"EXPERIMENTAL_RAG" if exact else "EXPERIMENTAL_RAG_REJECTED",
            "truth_state":"EXPERIMENTAL_UNVERIFIED" if exact else "UNKNOWN",
            "answer":"【未承認・検索拡張回答】"+r["answer"] if exact else None,
            "generated":generation,"candidate_id":r["id"],"source_id":r["source_id"],
            "reason":"evidence_exact_consistency" if exact else "generation_evidence_mismatch",
            "auto_promote":False}
