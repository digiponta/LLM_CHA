"""Minimal dialogue topic manager; does not authorize factual memory updates."""
import re
from dataclasses import dataclass

@dataclass
class TopicState:
    subject: str = ""
    expected: str = ""
    kind: str = "preference"

class TopicContext:
    def __init__(self):
        self.state=TopicState()

    def reset(self):
        self.state=TopicState()

    def respond_experience(self, utterance, evidence):
        """Keep reported product experiences separate from external evidence."""
        text=utterance.strip().rstrip("。！! ")
        for suffix, reply in (
            ("を食べました","そうなんですね。食べてみて、どうでしたか？"),
            ("を食べた","そうなんですね。食べてみて、味や食感はどうでしたか？"),
            ("を飲みました","飲んでみたんですね。どうでしたか？"),
            ("を飲んだ","そのドリンクを飲んだんですね。どんな味でしたか？"),
            ("も好きです","それも好きなんですね。どんなところが気に入っていますか？"),
            ("も好き","それも好きなんですね。どんなところが気に入っていますか？"),
            ("が好きです","好きなんですね。どんなところが気に入っていますか？"),
            ("が好き","好きなんですね。どんなところが気に入っていますか？"),
        ):
            if text.endswith(suffix):
                item=text[:-len(suffix)].strip()
                if len(item)>=2 and item in evidence:
                    self.state=TopicState(item,"taste","experience")
                    return reply
        if self.state.kind!="experience" or not self.state.subject:
            return None
        item=self.state.subject
        if any(w in text for w in ("美味しかった","おいしかった","美味しい","おいしい")):
            if any(w in text for w in ("あっさり","さっぱり","軽い味")):
                return f"あっさりした味わいが気に入ったんですね。{item}、また食べたいと思いますか？"
            return f"美味しかったんですね。{item}のどんなところが気に入りましたか？"
        if any(w in text for w in ("満足した","満足です","満足だった")):
            return f"満足できたんですね。{item}、いい食事になったようですね。"
        if any(w in text for w in ("また食べたい","リピートしたい")):
            return "また食べたいと思えるほど気に入ったんですね。"
        return None

    def respond(self,utterance):
        text=utterance.strip().rstrip("。！! ")
        match=re.fullmatch(r"私は[、,\s]*(.{2,80}?)が好き(?:です)?",text)
        if match:
            subject=match.group(1)
            self.state=TopicState(subject,"appeal")
            return f"{subject}が好きなんですね。どんなところに魅力を感じますか？"
        if not self.state.subject or self.state.kind!="preference":
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
