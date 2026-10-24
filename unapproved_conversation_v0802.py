"""v0.8.0.2: explicit Japanese conversational access to isolated Semantic evidence."""
from unapproved_semantic_search_v0801 import search_semantic

PREFIXES=("未承認知識で","未承認の知識で","未承認Semanticで","未承認データで")
def parse_unapproved_request(text):
    q=(text or "").strip()
    for prefix in PREFIXES:
        if q.startswith(prefix):
            question=q[len(prefix):].strip(" 、：:。")
            return question if question else None
    return None

def conversational_answer(question,path=None):
    evidence=search_semantic(question) if path is None else search_semantic(question,path)
    if evidence["status"]!="FOUND":
        return {"status":evidence["status"],
                "answer":"未承認Semantic候補には、この質問に対応する構造化根拠が見つからない。"}
    return {"status":"FOUND",
            "answer":evidence["answer"]+"\n出典："+evidence["source"]+"\n（未承認・外部資料・未検証）",
            "candidate_id":evidence["candidate_id"],"train_ready":False}
