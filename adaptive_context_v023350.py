"""LLM_CHA v0.2.35.0 — bounded, deterministic topic retention prototype.

Scores only metadata (recency, access count, explicit pin); does not inspect,
summarize or change user utterances, knowledge or Truth State. Eviction never
authorizes a proposition: restored history must still pass v0.2.34 gates.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class TopicScore:
    last_turn: int
    accesses: int = 1
    pinned: bool = False

class AdaptiveContext:
    def __init__(self, capacity: int = 8):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or not 1 <= capacity <= 16:
            raise ValueError("capacity must be 1..16")
        self.capacity=capacity
        self.turn=0
        self.topics: dict[str, TopicScore]={}

    def observe(self, topic: str, *, pin: bool = False) -> str | None:
        if not isinstance(topic,str) or not topic.strip() or len(topic)>128:
            raise ValueError("invalid topic")
        topic=topic.strip()
        self.turn+=1
        if topic in self.topics:
            entry=self.topics[topic]
            entry.last_turn=self.turn
            entry.accesses+=1
            entry.pinned=entry.pinned or pin
            return None
        if len(self.topics)==self.capacity:
            candidates=[(name,row) for name,row in self.topics.items() if not row.pinned]
            if not candidates:
                raise ValueError("all tracked topics pinned; no eviction permitted")
            # Least recently used first, then fewest accesses, then name.
            victim=min(candidates,key=lambda x:(x[1].last_turn,x[1].accesses,x[0]))[0]
            del self.topics[victim]
        else:
            victim=None
        self.topics[topic]=TopicScore(self.turn,1,pin)
        return victim

    def unpin(self,topic:str)->bool:
        if topic not in self.topics:
            return False
        self.topics[topic].pinned=False
        return True

    def retention_order(self)->tuple[str,...]:
        return tuple(name for name,_ in sorted(
            self.topics.items(),
            key=lambda x:(not x[1].pinned,-x[1].last_turn,-x[1].accesses,x[0])))

    def reset(self)->None:
        self.topics.clear()
        self.turn=0
