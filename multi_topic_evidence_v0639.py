"""v0.6.39 bounded multi-topic Wikipedia evidence context (session-local).
No external evidence is promoted or trained. Explicit restoration only.
"""
import re
from collections import OrderedDict

class TopicEvidenceContext:
    def __init__(self,max_topics=4):
        self.max_topics=max_topics
        self.items=OrderedDict()
        self.active=None
    def remember(self,topic,extract="",source=""):
        topic=str(topic).strip()
        if not topic:return
        record={"topic":topic,"extract":str(extract or ""),"source":str(source or ""),
                "truth_state":"EXTERNAL_UNVERIFIED"}
        self.items.pop(topic,None)
        self.items[topic]=record
        while len(self.items)>self.max_topics:
            old,_=self.items.popitem(last=False)
            if self.active==old:self.active=None
        self.active=topic
    def current(self):
        return self.items.get(self.active) if self.active else None
    def restore(self,utterance):
        match=re.fullmatch(r"(.+?)に戻って[。！! ]*",utterance.strip())
        if not match:return None
        requested=match.group(1).strip()
        exact=self.items.get(requested)
        if exact is None:
            return {"status":"NOT_FOUND","requested":requested}
        self.items.move_to_end(requested)
        self.active=requested
        return {"status":"RESTORED",**exact}
    def reset(self):
        self.items.clear()
        self.active=None
