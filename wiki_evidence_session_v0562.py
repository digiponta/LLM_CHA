"""v0.5.62 track distinct Wikipedia evidence across repeated 'more' requests.
Session-local state only. Evidence must be from the same article.
"""
from wiki_more_details_v0560 import more

class EvidenceSession:
    def __init__(self):
        self.identity=None
        self.seen=set()
    def reset(self):
        self.identity=None
        self.seen.clear()
    def next(self,wiki,question,persona="nagato",fetch=None):
        if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
            self.reset()
            return {"status":"NO_CONTEXT"}
        identity=(wiki.get("title"),wiki.get("url"))
        if identity!=self.identity:
            self.identity=identity
            self.seen=set()
        # Calls to more use a bounded same-article 4000-character extract.
        # The first retrieval remains governed by its original source checks.
        result=more(wiki,question,persona=persona,fetch=fetch)
        if result.get("status")!="FOUND":
            return result
        # v0.5.60 only returns the first eligible sentence. Suppress repeats
        # rather than presenting a duplicate as new knowledge.
        answer=result.get("answer","")
        if answer in self.seen:
            return {"status":"EVIDENCE_EXHAUSTED","source":wiki.get("url"),
                    "verified":False,"train_ready":False}
        self.seen.add(answer)
        result["route"]="PERSONA_WIKIPEDIA_EVIDENCE_SESSION"
        return result
