"""LLM_CHA v0.3.6 shadow-mode adaptive retention adapter.

Shadow only: the real MultiTopicContext remains the sole routing authority.
Never modify its topics, decisions, Truth State, or proposition cursor.
"""
from __future__ import annotations
from admission_forgetting_v0350 import evaluate
from adaptive_retention_eval_v023351 import Event

class RetentionShadow:
    def __init__(self, capacity=8):
        if type(capacity) is not int or not 1<=capacity<=16:
            raise ValueError("capacity")
        self.capacity=capacity
        self.events=[]
        self.last=None

    def observe_route(self, route):
        if getattr(route,"action",None)!="READY":
            return None
        topic=getattr(route,"topic",None)
        if not isinstance(topic,str) or not topic.strip():
            return None
        # Topic names are metadata, never treated as facts.
        self.events.append(Event("observe",topic))
        self.last=evaluate(self.events,capacity=self.capacity)
        return self.last

    def reset(self):
        self.events.clear()
        self.last=None

    def stats(self):
        result=dict(self.last) if self.last is not None else {}
        return {"mode":"shadow","observed_events":len(self.events),
                "capacity":self.capacity,"retention":result}
