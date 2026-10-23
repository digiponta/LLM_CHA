"""v0.7.17 conservative lexical retrieval for Experimental Semantic Memory.

A separate candidate knowledge store is used; Approved data and weights are
never modified. Retrieval is evidence for routing, not factual validation.
"""
import re
from dual_semantic_memory_v071 import DualMemory

STOP={"v079","実験","符号","何","何ですか","教えて","対応","する","とは","の","は"}
def tokens(text):
    return set(re.findall(r"[一-龯ぁ-んァ-ヶー]+|[A-Za-z]+|[0-9]+",str(text).lower()))-STOP

def retrieve(memory,question,*,min_overlap=2):
    pending=[x for x in memory.candidates() if x["status"]=="PENDING"]
    query=tokens(question)
    scored=[]
    for row in pending:
        words=tokens(row["question"])
        overlap=len(query & words)
        if overlap>=min_overlap:
            scored.append((overlap,row))
    scored.sort(key=lambda x:x[0],reverse=True)
    if not scored:return {"status":"UNKNOWN","reason":"no_candidate","record":None}
    if len(scored)>1 and scored[0][0]==scored[1][0]:
        return {"status":"UNKNOWN","reason":"ambiguous","record":None}
    return {"status":"MATCH","reason":"lexical_overlap","record":scored[0][1]}

def route(memory,question,*,min_overlap=2):
    hit=retrieve(memory,question,min_overlap=min_overlap)
    if hit["status"]!="MATCH":
        return {"route":"EXPERIMENTAL_UNKNOWN","answer":None,"truth_state":"UNKNOWN",
                "reason":hit["reason"],"auto_promote":False}
    row=hit["record"]
    return {"route":"EXPERIMENTAL_MEMORY_EVIDENCE","answer":"【未承認・候補知識】"+row["answer"],
            "truth_state":"EXPERIMENTAL_UNVERIFIED",
            "candidate_id":row["id"],"source_id":row["source_id"],
            "reason":hit["reason"],"auto_promote":False}
