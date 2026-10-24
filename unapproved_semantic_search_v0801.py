"""v0.8.0.1: exact evidence-backed search over isolated Semantic tuples.

Only explicitly extracted, unapproved Wikipedia statements are eligible.
This is a retrieval adapter, not a trained secondary LLM.
"""
from unapproved_llm_intake_v074446 import _read,DEFAULT_STORE
from unapproved_llm_compare_v074447 import requires_context

# v0.8.0.6: conservative paraphrase matching; no inferred subjects.
RELATION_CUES={
    "is_basic_unit":("とは","何","基本単位","どういうもの","どんなもの","説明して","教えて"),
    "is":("とは","何","定義","どういうもの","どんなもの"),
    "can_have_superposition":("重ね合わせ","状態","できる","同時に"),
    "can_take_state":("状態","重ね合わせ","とる"),
    "represents":("表現","何","とは","どう表す"),
}

def search_semantic(question,path=DEFAULT_STORE):
    q=(question or "").strip()
    if not q:return {"status":"INVALID_QUESTION"}
    rows=_read(path)["candidates"]
    hits=[]
    for row in rows:
        if row.get("state")!="UNAPPROVED" or row.get("truth_state")!="EXTERNAL_UNVERIFIED":
            continue
        semantic=row.get("semantic_candidate") or {}
        if semantic.get("status")!="STRUCTURED":continue
        subject=semantic.get("subject","")
        if not subject or subject not in q:continue
        relation=semantic.get("relation","")
        # Do not guess a relation from arbitrary free-form wording.
        matches=RELATION_CUES.get(relation,())
        if not any(word in q for word in matches):continue
        if requires_context(row.get("natural_language","")):continue
        score=(2 if relation=="is_basic_unit" and "とは" in q else 0)+len([word for word in matches if word in q])
        hits.append((score,row,semantic))
    if not hits:
        return {"status":"NO_STRUCTURED_MATCH","train_ready":False}
    hits.sort(key=lambda hit:(-hit[0],hit[1]["id"]))
    _,row,semantic=hits[0]
    return {"status":"FOUND","subject":semantic["subject"],
            "relation":semantic["relation"],"object":semantic["object"],
            "answer":"【未承認Semantic候補・外部資料・未検証】"+row["natural_language"],
            "source":row["source"],"candidate_id":row["id"],
            "model_generated":False,"train_ready":False,
            "truth_state":"EXTERNAL_UNVERIFIED","approved_memory_changed":False}
