"""Session-only preference and impression dialogue context.

No persistence, model training, or external-evidence promotion.
"""
import re
from dataclasses import dataclass, field

COLORS=("黄色","赤色","青色","緑色","オレンジ色","紫色","白色","黒色","ピンク色","黄色い","赤い","青い","緑の")

@dataclass
class PreferenceContext:
    topic: str = ""
    preferences: list = field(default_factory=list)
    def set_topic(self, topic):
        self.topic=(topic or "").strip()
    def respond(self, utterance):
        text=(utterance or "").strip().rstrip("。")
        if not text or text.startswith("/") or "？" in text or "?" in text:
            return None
        if not self.topic:
            return None
        # Explicit positive preference for the current topic, no inferred persistence.
        m=re.fullmatch(r"(?:私は[、,]?\s*)?(.{1,50}?)が好き(?:です|だ|なんです)?",text)
        if m:
            thing=m.group(1).strip()
            if thing==self.topic:
                self.preferences.append({"topic":self.topic,"kind":"topic","value":thing})
                return f"{self.topic}が好きなんだね。どんなところが気に入っているの？"
            if any(c in thing for c in COLORS):
                self.preferences.append({"topic":self.topic,"kind":"color","value":thing})
                return f"{thing}の{self.topic}が好きなんだね。"
            self.preferences.append({"topic":self.topic,"kind":"other","value":thing})
            return f"{thing}が好きなんだね。"
        if re.search(r"きらきら|キラキラ|輝き|光沢|ファイア",text) and re.search(r"心地よ|好き|きれい|綺麗|美しい",text):
            self.preferences.append({"topic":self.topic,"kind":"impression","value":text})
            return f"{self.topic}の輝きが心地よいんだね。"
        return None
