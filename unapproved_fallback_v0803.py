"""v0.8.0.3: conservative unapproved evidence fallback.

Only respond when an upstream route explicitly reports failure. The caller
must not treat Wikipedia-derived content as verified or trainable.
"""
from unapproved_semantic_search_v0801 import search_semantic

def fallback_on_failure(question, failed, path=None):
    if not failed:
        return {"status":"NOT_NEEDED"}
    evidence=search_semantic(question) if path is None else search_semantic(question,path)
    if evidence.get("status")!="FOUND":
        return {"status":"NO_FALLBACK","reason":evidence.get("status")}
    return {"status":"FOUND","answer":evidence["answer"]+"\n出典："+evidence["source"]+"\n（未承認・外部資料・未検証）",
            "source":evidence["source"],"candidate_id":evidence["candidate_id"],
            "train_ready":False,"model_generated":False,"truth_state":"EXTERNAL_UNVERIFIED"}
