"""v0.5.37 conservative comparison of source-backed atomic propositions.

CONFLICT is restricted to explicit negation of the same atomic relation.
Different properties are complements, not necessarily contradictions.
"""
from wiki_typed_propositions_v0532 import extract
from wiki_independent_propositions_v0537 import extract_independent

def collect(sentence,source=None):
    return extract(sentence,source)+extract_independent(sentence,source)

def compare(left,right):
    required=("subject","predicate","object","source")
    if not all(isinstance(p,dict) and all(isinstance(p.get(k),str) for k in required) for p in (left,right)):
        return {"status":"INSUFFICIENT","reason":"INVALID_PROPOSITION"}
    if left["subject"]!=right["subject"]:
        return {"status":"INSUFFICIENT","reason":"DIFFERENT_SUBJECT"}
    if left["predicate"]!=right["predicate"]:
        return {"status":"COMPLEMENT","reason":"DIFFERENT_PREDICATE"}
    a,b=left["object"],right["object"]
    if a==b:return {"status":"MATCH","reason":"EXACT_TRIPLE"}
    if a=="非"+b or b=="非"+a:
        return {"status":"CONFLICT","reason":"EXPLICIT_NEGATION_CANDIDATE"}
    return {"status":"INSUFFICIENT","reason":"SAME_PREDICATE_DIFFERENT_OBJECT"}
def compare_all(records,max_pairs=120):
    result=[]
    for i,a in enumerate(records):
        for j in range(i+1,len(records)):
            if len(result)>=max_pairs:return result
            b=records[j]
            judgment=compare(a,b)
            result.append({"left":i,"right":j,**judgment,
                           "sources":[a.get("source"),b.get("source")],
                           "verified":False,"train_ready":False})
    return result
