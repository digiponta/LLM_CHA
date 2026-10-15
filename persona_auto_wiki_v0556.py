"""v0.5.56 automatic unverified Wikipedia enrichment for persona sharing.

Only explicit article subjects or conservatively detected term candidates are
eligible. Never learn/promote retrieved material. Fail closed to the existing
persona sharing answer. Lookup and response functions are injected for tests.
"""
from persona_conversation_router_v0549 import classify
from unknown_term_detection_v0516 import detect, KNOWN

def candidate(user,known=None):
    known=set(KNOWN if known is None else known)
    intent=classify(user)
    if intent["intent"]=="ARTICLE_SHARING":
        term=intent["topic"]
        if term not in known and len(term)<=60:
            return term
    for term in detect(user,known=known):
        return term
    return None

def enrich(user,persona,lookup,render,cache=None,known=None):
    term=candidate(user,known)
    if not term:
        return {"status":"NO_CANDIDATE","term":None,"answer":None}
    if cache is not None and term in cache:
        info=cache[term]
    else:
        try:
            info=lookup(term,context=user)
        except (OSError,ValueError,TimeoutError,KeyError) as exc:
            return {"status":"LOOKUP_FAILED","term":term,"answer":None,
                    "reason":type(exc).__name__}
        if cache is not None:
            cache[term]=info
    if info.get("status")!="FOUND":
        return {"status":info.get("status","LOOKUP_FAILED"),"term":term,"answer":None}
    response=render(info,user,persona=persona)
    if not response or not response.get("answer"):
        return {"status":"NO_GROUNDED_RESPONSE","term":term,"answer":None}
    return {"status":"FOUND","term":term,"answer":response["answer"],
            "source":response.get("source"),"url":info.get("url"),
            "wiki_context":info,"route":"PERSONA_AUTO_WIKIPEDIA",
            "truth_state":"EXTERNAL_UNVERIFIED","verified":False,
            "train_ready":False,"auto_promote":False,"auto_learn":False}
