"""Minimal dialogue topic manager; does not authorize factual memory updates."""
import re
from dataclasses import dataclass

@dataclass
class TopicState:
    subject: str = ""
    expected: str = ""

class TopicContext:
    def __init__(self):
        self.state=TopicState()

    def reset(self):
        self.state=TopicState()

    def respond(self,utterance):
        text=utterance.strip().rstrip("。！! ")
        match=re.fullmatch(r"私は[、,\s]*(.{2,80}?)が好き(?:です)?",text)
        if match:
            subject=match.group(1)
            self.state=TopicState(subject,"appeal")
            return f"{subject}が好きなんですね。どんなところに魅力を感じますか？"
        if not self.state.subject:
            return None
        subject=self.state.subject
        if self.state.expected=="appeal":
            if any(x in text for x in ("きらきら","キラキラ","輝き")):
                self.state.expected="color"
                return f"輝くところが好きなんですね。{subject}のどんな色合いが好みですか？"
            if any(x in text for x in ("心地よい","綺麗","きれい")):
                self.state.expected="color"
                return f"そう感じるんですね。{subject}のどんな色合いが好みですか？"
        if self.state.expected=="color":
            if re.fullmatch(r".{1,24}(?:色|黄|赤|青|緑|紫|白|黒|オレンジ|琥珀色).{0,12}(?:好き|好み)(?:です)?",text):
                self.state.expected="ack"
                return f"その色合いが好みなんですね。{subject}の輝きとよく合いそうですね。"
        if text in ("そうだよ","そうです","うん","はい","そうそう"):
            return f"そうなんですね。{subject}の魅力が伝わってきます。"
        return None
