"""v0.5.57: Wikipedia fallback for explicitly UNKNOWN knowledge requests.

Never override truth blocks or stale-checkpoint decisions. External source
material remains unverified and never becomes learned/verified knowledge.
"""
def fallback(concept, utterance, persona, lookup, render, grounded=None, cache=None):
    if not isinstance(concept,str) or not concept.strip() or len(concept.strip())>60:
        return {"status":"INVALID_CONCEPT"}
    concept=concept.strip()
    try:
        if cache is not None and concept in cache:
            wiki=cache[concept]
        else:
            wiki=lookup(concept,context=utterance)
            if cache is not None and wiki.get("status")=="FOUND":
                cache[concept]=wiki
    except (OSError, ValueError, KeyError, TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","reason":type(exc).__name__}
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":wiki.get("status","LOOKUP_FAILED") if isinstance(wiki,dict) else "LOOKUP_FAILED"}
    answer=render(wiki,utterance,persona=persona)
    if answer is None and grounded is not None:
        answer=grounded(wiki,utterance)
    if not isinstance(answer,dict) or not answer.get("answer"):
        return {"status":"NO_GROUNDED_ANSWER"}
    return {"status":"FOUND","term":concept,"answer":answer["answer"],
            "route":"UNKNOWN_WIKIPEDIA_FALLBACK","url":wiki.get("url"),
            "source":answer.get("source",wiki.get("url")),
            "wiki_context":wiki,"truth_state":"EXTERNAL_UNVERIFIED",
            "verified":False,"train_ready":False,"auto_promote":False,"auto_learn":False}
