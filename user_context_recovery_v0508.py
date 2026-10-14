"""LLM_CHA v0.5.8: conservative user-context retention and recovery.

The recovery is a clearly identified template, NOT a KNOWN model generation,
a verified fact, a training pair or a trusted AI context turn.
"""
from dataclasses import dataclass

CONTINUATION=("続きの話","続きを","その話","さっきの話")
MOVIES=("アベンジャーズ",)
TOPICS={"映画":("映画","アベンジャーズ","マーベル","シネマ"),
        "音楽":("音楽","曲","歌","ライブ")}

@dataclass
class UserContext:
    topic: str|None=None
    subject: str|None=None

    def observe(self,text):
        for topic,terms in TOPICS.items():
            if any(term in text for term in terms):
                self.topic=topic
                break
        for movie in MOVIES:
            if movie in text:
                self.subject=movie
                self.topic="映画"
        if self.topic!="映画":
            self.subject=None

    def continuation(self,text):
        return any(token in text for token in CONTINUATION)

    def recovery(self,text):
        if not self.topic:
            return None
        if self.topic=="映画":
            if self.subject:
                if self.continuation(text):
                    return f"{self.subject}の話ですね。お気に入りの登場人物はいますか？"
                return f"{self.subject}がお好きなんですね。どの作品が特に好きですか？"
            return "映画の話ですね。どんな映画が好きですか？"
        if self.topic=="音楽":
            return "音楽の話ですね。どんな曲やアーティストが好きですか？"
        return None
