"""Conservative short-turn semantic context and response surface repairs (v0.9.7.55).
Conversation-local; never verifies a source or promotes knowledge.
"""
from dataclasses import dataclass
import re

@dataclass
class Carryover:
    pending_topic: str|None = None
    def observe(self, utterance):
        s=str(utterance or "").strip()
        if "とは" in s or s.startswith("/"):
            self.pending_topic=None
            return None
        m=re.fullmatch(r"(.{2,55}?)の(?:成分|化学組成)は[？?。 ]*",s)
        if m:
            self.pending_topic=m.group(1)
            return f"{self.pending_topic}の化学組成について知りたい？"
        if self.pending_topic and re.fullmatch(r"(?:化学組成|成分)(?:を知りたい|は何|を教えて|について知りたい)[。？? ]*",s):
            t=self.pending_topic
            self.pending_topic=None
            return f"{t}の化学組成についての質問だね。資料に基づく確認が必要。"
        if len(s)>40 or re.search(r"[。！？?]",s):
            self.pending_topic=None
        return None

def repair_preference_object(text):
    s=str(text or "").strip()
    # Strip the terminal case marker only, never arbitrary internal characters.
    return re.sub(r"(?:が|は)$","",s)

def evaluation(text):
    s=str(text or "").strip().rstrip("。！! ")
    if s in ("きれい","きれいです","綺麗","綺麗です","美しい","美しいです"):
        return "そう。"
    return None
