"""Conversation-local topic-keyed question context (v0.9.7.56).

Never fabricates factual evidence; unresolved questions receive an
explicit source-needed response instead of being passed to Unknown Gate.
"""
from dataclasses import dataclass,field
import re

ATTR=r"(?:化学組成|成分)"
EXPLICIT=re.compile(r"^(?P<topic>[^。！？?\n]{2,55}?)の"+ATTR+r"(?:は|を知りたい|を教えて|について知りたい)?[？?。 ]*$")
FOLLOWUP=re.compile(r"^(?:化学組成|成分)(?:を知りたい|は何|を教えて|について知りたい)?[？?。 ]*$")
TRAIL=re.compile(r"^(?P<topic>[^。！？?\n]{2,55}?)の"+ATTR+r"は[？?。 ]*$")
@dataclass
class TopicContext:
    active_topic:str|None=None
    topics:dict=field(default_factory=dict)
    def observe(self,text):
        s=str(text or "").strip()
        if not s or s.startswith("/"):return None
        if "とは" in s:return None
        m=EXPLICIT.fullmatch(s)
        if m:
            topic=m.group("topic").strip()
            if not topic:return None
            self.active_topic=topic
            self.topics[topic]={"attribute":"化学組成","status":"SOURCE_NEEDED"}
            if TRAIL.fullmatch(s):
                return f"{topic}の化学組成について知りたい？"
            return f"{topic}の化学組成についての質問だね。資料に基づく確認が必要。"
        if FOLLOWUP.fullmatch(s) and self.active_topic in self.topics:
            return f"{self.active_topic}の化学組成についての質問だね。資料に基づく確認が必要。"
        return None
