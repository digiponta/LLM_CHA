"""v0.2.34.0: transient long-term conversation checkpoint (experimental).

No serialization of chat text, personal data, model weights or Truth State.
Snapshot preserves only topic names, proposition IDs and cursor offsets.
No automatic disk writes; caller explicitly exports/imports snapshots.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
import json

SCHEMA = "llm-cha-context-v02340"
MAX_TOPICS=16
MAX_IDS=512

@dataclass
class ContextCheckpoint:
    topics: dict[str,list[str]] = field(default_factory=dict)
    active_topic: str|None = None

    def remember(self,topic:str,proposition_id:str)->None:
        if not topic or len(topic)>128 or not proposition_id or len(proposition_id)>128:
            raise ValueError("invalid topic or proposition identifier")
        if topic not in self.topics and len(self.topics)>=MAX_TOPICS:
            raise ValueError("topic capacity exceeded")
        ids=self.topics.setdefault(topic,[])
        if proposition_id not in ids:
            if sum(map(len,self.topics.values()))>=MAX_IDS:
                raise ValueError("proposition capacity exceeded")
            ids.append(proposition_id)
        self.active_topic=topic

    def switch(self,topic:str)->bool:
        if topic not in self.topics:
            return False
        self.active_topic=topic
        return True

    def reset(self)->None:
        self.topics.clear()
        self.active_topic=None

    def export(self)->str:
        state={"schema":SCHEMA,"topics":self.topics,"active_topic":self.active_topic}
        return json.dumps(state,ensure_ascii=False,sort_keys=True,separators=(",",":"))

    @classmethod
    def restore(cls,data:str)->"ContextCheckpoint":
        obj=json.loads(data)
        if not isinstance(obj,dict) or obj.get("schema")!=SCHEMA:
            raise ValueError("unsupported checkpoint schema")
        topics=obj.get("topics")
        active=obj.get("active_topic")
        if not isinstance(topics,dict) or len(topics)>MAX_TOPICS:
            raise ValueError("invalid topic map")
        result=cls()
        for topic,ids in topics.items():
            if not isinstance(topic,str) or not topic or len(topic)>128 or not isinstance(ids,list):
                raise ValueError("invalid topic entry")
            if len(ids)!=len(set(ids)):
                raise ValueError("duplicate proposition identifiers")
            for pid in ids:
                result.remember(topic,pid)
            if not ids:
                result.topics[topic]=[]
        if active is not None and (not isinstance(active,str) or active not in topics):
            raise ValueError("invalid active topic")
        result.active_topic=active
        return result

    def digest(self)->str:
        return sha256(self.export().encode("utf-8")).hexdigest()
