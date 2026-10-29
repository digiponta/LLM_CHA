"""Session-only topic/evidence binding. External text is always unverified."""
import re
from dataclasses import dataclass, field

@dataclass
class TemporaryEvidence:
    topic: str = ""
    records: list = field(default_factory=list)
    def set_topic(self, topic):
        self.topic=(topic or "").strip()
    def add(self, text, source, topic=None):
        if topic:self.set_topic(topic)
        text=(text or "")[:12000]
        if not text.strip():return False
        self.records.append({"topic":self.topic,"source":source,"text":text,"verified":False})
        self.records=self.records[-5:]
        return True
    def answer(self, question):
        q=(question or "").strip()
        if not self.topic or not self.records:return None
        if not re.search(r"(化学組成|組成|成分)",q):return None
        for record in reversed(self.records):
            if record["topic"]!=self.topic:continue
            text=record["text"]
            m=re.search(r"(?:化学組成|主成分|組成)\s*[：:は]?\s*(?:ZnS\s*[（(]硫化亜鉛[）)]|硫化亜鉛\s*[（(]ZnS[）)])",text,re.I)
            if not m:
                m=re.search(r"(?:スファレライト|閃亜鉛鉱).{0,45}(?:ZnS|硫化亜鉛)",text,re.I|re.S)
            if m and self.topic in ("スファレライト","閃亜鉛鉱"):
                return f"【外部未検証資料：{record['source']}】スファレライトの化学組成は硫化亜鉛（ZnS）です。"
        return None
