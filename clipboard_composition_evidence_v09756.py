"""Temporary source-grounded composition lookup (v0.9.7.56).

Evidence is only the user-copied page, explicitly unverified.
Never turn a source passage into a trusted semantic fact.
"""
import re

TOPIC=re.compile(r"スファレライト|閃亜鉛鉱|sphalerite",re.IGNORECASE)
CHEM=re.compile(r"(?:化学組成|組成|成分)[^。\n]{0,100}?(?:硫化亜鉛\s*[（(]\s*ZnS\s*[）)]|ZnS\s*[（(]\s*硫化亜鉛\s*[）)])|硫化亜鉛\s*[（(]\s*ZnS\s*[）)]")
TOPIC_QUERY=re.compile(r"スファレライト|閃亜鉛鉱",re.IGNORECASE)
ASK=re.compile(r"化学組成|成分|組成")
FOLLOWUP=re.compile(r"^(?:化学組成|成分|組成)(?:を知りたい|は|について|を教えて)?[。？? ]*$")

class CompositionContext:
    def __init__(self):
        self.topic=None
        self.attribute=None
    def reset(self):
        self.topic=None
        self.attribute=None
    def answer(self,utterance,source):
        q=str(utterance or "").strip()
        text=str(source or "")
        if not text:return None
        explicit=bool(TOPIC_QUERY.search(q))
        if explicit and (ASK.search(q) or q.endswith("の成分")):
            self.topic="スファレライト" if "スファレライト" in q else "閃亜鉛鉱"
            self.attribute="化学組成"
        elif explicit and self.topic is None:
            self.topic="スファレライト" if "スファレライト" in q else "閃亜鉛鉱"
        if not ASK.search(q):return None
        if not explicit and not (self.topic and FOLLOWUP.fullmatch(q)):return None
        if not self.topic:return None
        # Keep evidence local to a text window containing the mineral name,
        # not a detached ZnS mention elsewhere on the page.
        match=None
        for m in TOPIC.finditer(text):
            window=text[max(0,m.start()-100):m.end()+200]
            if CHEM.search(window):
                match=window
                break
        if match is None:
            return f"{self.topic}の化学組成についての質問だね。取得済み資料から根拠を確認できなかった。（外部情報・未検証）"
        return (f"コピーした資料には、{self.topic}について「化学組成が硫化亜鉛（ZnS）の鉱物」と"
                "記載されています。（クリップボード由来・未検証）")
