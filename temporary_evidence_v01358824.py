"""Session-only, label-based Evidence extraction. External text stays unverified.

Only explicitly labeled values from a document about the active topic qualify.
No generated facts, learning, or persistent memory writes.
"""
import re
from dataclasses import dataclass, field

ATTRS = {
    "化学組成": (r"化学組成|主成分|組成|成分", ("化学組成", "主成分", "組成")),
    "モース硬度": (r"モース硬度|硬度", ("モース硬度", "硬度")),
    "屈折率": (r"屈折率", ("屈折率",)),
    "分散率": (r"分散率|ファイアの強さ", ("分散率",)),
    "産地": (r"産地|産出地|どこで採れ|どこで産出", ("産地", "産出地")),
}
ALIASES = {"スファレライト": ("スファレライト", "閃亜鉛鉱", "sphalerite"),
           "閃亜鉛鉱": ("スファレライト", "閃亜鉛鉱", "sphalerite")}
MAX_VALUE = 240

def attribute_from_question(question):
    for attr, (pattern, _) in ATTRS.items():
        if re.search(pattern, question, re.I):
            return attr
    return None

def extract_attribute(text, attr):
    _, labels = ATTRS[attr]
    for line in text.splitlines():
        line=line.strip().lstrip("・*- ")
        for label in labels:
            # Explicit property labels only, not sentences that merely contain a keyword.
            m=re.match(r"^"+re.escape(label)+r"\s*[：:]\s*(.+)$",line)
            if not m:
                continue
            value=m.group(1).strip()
            if value and len(value)<=MAX_VALUE and not re.search(r"(?i)(https?://|<script)",value):
                return value
    return None

@dataclass
class TemporaryEvidence:
    topic: str = ""
    records: list = field(default_factory=list)
    def set_topic(self, topic):
        new=(topic or "").strip()
        if new != self.topic:
            self.topic=new
    def add(self, text, source, topic=None):
        if topic:
            self.set_topic(topic)
        text=(text or "")[:12000]
        if not text.strip():
            return False
        self.records.append({"topic":self.topic,"source":source,"text":text,"verified":False})
        self.records=self.records[-5:]
        return True
    def answer(self, question):
        attr=attribute_from_question((question or "").strip())
        if not attr or not self.topic or not self.records:
            return None
        aliases=ALIASES.get(self.topic,(self.topic,))
        for record in reversed(self.records):
            if record["topic"]!=self.topic:
                continue
            text=record["text"]
            if not any(alias.lower() in text.lower() for alias in aliases):
                continue
            value=extract_attribute(text,attr)
            if not value:
                continue
            return f"【外部未検証資料：{record['source']}】{self.topic}の{attr}は{value}です。"
        return None
