"""v0.5.20: persona-consistent, evidence-bounded Wikipedia follow-ups.

A sentence is quoted only when supported by the fetched extract.
Intent-based follow-ups never invent explanations not present in evidence.
"""
import re
from wiki_fragment_gate_v074428 import coherent_scientific_evidence

FOLLOWUPS={"もう少し詳しく","詳しく教えて","もっと詳しく","その続き","続きを教えて","それについて詳しく"}
WHY=("なぜ","どうして","理由","原理")
USE=("何に使","用途","応用","どこで使")
class WikiConversation:
    def __init__(self,persona="nagato"):
        self.current=None
        self.used=set()
        self.persona=persona if persona in ("nagato","neutral") else "neutral"
    def clear(self):
        self.current=None
        self.used=set()
    def offer(self,wiki):
        if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
            self.clear()
            return
        self.current=wiki.copy()
        self.used={0}
    def _answer(self,sentence):
        sentence=sentence.rstrip("。")+"。"
        if self.persona=="nagato":
            return "Wikipediaには、"+sentence+"とある。"
        return "Wikipediaには、"+sentence+"と記載されています。"
    def respond(self,text):
        q=text.strip().rstrip("。！？!? ")
        if self.current is None:return None
        kind="why" if any(t in q for t in WHY) else ("use" if any(t in q for t in USE) else ("more" if q in FOLLOWUPS else None))
        if kind is None:
            self.clear()
            return None
        extract=self.current.get("extract","")
        parts=[p.strip() for p in re.split(r"[。\n]",extract) if 15<=len(p.strip())<=180]
        # Sentences are indexed consistently to avoid repeating evidence.
        patterns={"why":("原理","ジョセフソン","接合","なぜ","量子干渉","仕組み"),
                  "use":("医療","応用","用途","利用され","使われ","用いら","利用")}
        order=list(enumerate(parts))
        if kind=="use":
            order.sort(key=lambda item: -sum(1 for keyword in ("医療","応用","用途","利用され","使われ") if keyword in item[1]))
        for i,p in order:
            if i in self.used:continue
            if not coherent_scientific_evidence(p):
                self.used.add(i)
                continue
            if kind!="more" and not any(k in p for k in patterns[kind]):continue
            self.used.add(i)
            return {"answer":self._answer(p),"route":"PERSONA_WIKIPEDIA_CONTEXT_FOLLOWUP",
                    "source":self.current["url"],"persona":self.persona,
                    "quality_gate":"SOURCE_SPAN_EXACT",
                    "verified":False,"train_ready":False}
        msg=("取得した資料には、その質問に答える明確な根拠がない。"
             if self.persona=="nagato" else
             "取得した資料には、その質問に答える明確な根拠がありません。")
        return {"answer":msg,"route":"WIKIPEDIA_EVIDENCE_INSUFFICIENT",
                "source":self.current.get("url"),"persona":self.persona,
                "quality_gate":"NO_SUPPORTED_SENTENCE",
                "verified":False,"train_ready":False}
