"""v0.7.17 conservative lexical retrieval for Experimental Semantic Memory.

A separate candidate knowledge store is used; Approved data and weights are
never modified. Retrieval is evidence for routing, not factual validation.
"""
import re
from dual_semantic_memory_v071 import DualMemory

def grams(text):
    compact=re.sub(r"[^一-龯ぁ-んァ-ヶーa-z0-9]","",str(text).lower())
    return {compact[i:i+3] for i in range(max(0,len(compact)-2))}

def retrieve(memory,question,*,min_overlap=1):
    pending=[x for x in memory.candidates() if x["status"]=="PENDING"]
    query=grams(question)
    corpus=[grams(row["question"]) for row in pending]
    # Remove common n-grams occurring in multiple unrelated candidates;
    # this prevents generic prompts like 'v079実験の符号' from matching.
    from collections import Counter
    frequency=Counter(g for features in corpus for g in features)
    scored=[]
    for row,features in zip(pending,corpus):
        rare={g for g in query & features if frequency[g]==1}
        if len(rare)>=min_overlap:
            scored.append((len(rare),row))
    scored.sort(key=lambda pair:pair[0],reverse=True)
    if not scored:return {"status":"UNKNOWN","reason":"no_candidate","record":None}
    if len(scored)>1 and scored[0][0]==scored[1][0]:
        return {"status":"UNKNOWN","reason":"ambiguous","record":None}
    return {"status":"MATCH","reason":"unique_character_trigrams","record":scored[0][1]}

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
