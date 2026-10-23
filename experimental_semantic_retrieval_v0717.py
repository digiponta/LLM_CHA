"""v0.7.17 conservative lexical retrieval for Experimental Semantic Memory.

A separate candidate knowledge store is used; Approved data and weights are
never modified. Retrieval is evidence for routing, not factual validation.
"""
import re
from dual_semantic_memory_v071 import DualMemory

def grams(text):
    compact=re.sub(r"[^一-龯ぁ-んァ-ヶーa-z0-9]","",str(text).lower())
    return {compact[i:i+3] for i in range(max(0,len(compact)-2))}

def salient_grams(text):
    # Remove question boilerplate BEFORE matching. Generic phrases like
    # 'の符号' must not authorize a Candidate when only one record exists.
    normalized=str(text).lower()
    normalized=re.sub(r"v[0-9]+", "", normalized)
    for word in ("実験","について","対応する","何ですか","教えてください",
                 "教えて","符号","番号","とは","ですか"):
        normalized=normalized.replace(word,"")
    normalized=re.sub(r"[のはをでにがと？?、。\\s]", "", normalized)
    compact=re.sub(r"[^一-龯ぁ-んァ-ヶーa-z0-9]", "", normalized)
    return {compact[i:i+2] for i in range(max(0,len(compact)-1))}

def retrieve(memory,question,*,min_overlap=1):
    pending=[x for x in memory.candidates() if x["status"]=="PENDING"]
    query=salient_grams(question)
    if not query:
        return {"status":"UNKNOWN","reason":"no_salient_query","record":None}
    corpus=[salient_grams(row["question"]) for row in pending]
    scored=[]
    for row,features in zip(pending,corpus):
        overlap=len(query & features)
        if overlap>=min_overlap:
            scored.append((overlap,row))
    scored.sort(key=lambda pair:pair[0],reverse=True)
    if not scored:return {"status":"UNKNOWN","reason":"no_candidate","record":None}
    if len(scored)>1 and scored[0][0]==scored[1][0]:
        return {"status":"UNKNOWN","reason":"ambiguous","record":None}
    return {"status":"MATCH","reason":"salient_character_bigrams","record":scored[0][1]}

def route(memory,question,*,min_overlap=1):
    hit=retrieve(memory,question,min_overlap=min_overlap)
    if hit["status"]!="MATCH":
        return {"route":"EXPERIMENTAL_UNKNOWN","answer":None,"truth_state":"UNKNOWN",
                "reason":hit["reason"],"auto_promote":False}
    row=hit["record"]
    return {"route":"EXPERIMENTAL_MEMORY_EVIDENCE","answer":"【未承認・候補知識】"+row["answer"],
            "truth_state":"EXPERIMENTAL_UNVERIFIED",
            "candidate_id":row["id"],"source_id":row["source_id"],
            "reason":hit["reason"],"auto_promote":False}
