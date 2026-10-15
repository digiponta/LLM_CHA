"""v0.5.18: bounded source-grounded Wikipedia conversation context.

No neural generation or promotion to trusted Semantic Memory. A follow-up
can quote another sentence from the same cited article only once, and unrelated
inputs invalidate the pending context.
"""
import re

FOLLOWUPS={"もう少し詳しく","詳しく教えて","もっと詳しく","その続き","続きを教えて","それについて詳しく"}
class WikiConversation:
    def __init__(self):
        self.current=None
        self.turn=0
    def clear(self):
        self.current=None
        self.turn=0
    def offer(self,wiki):
        if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
            self.clear()
            return
        self.current=wiki.copy()
        self.turn=0
    def respond(self,text):
        text=text.strip().rstrip("。！？!? ")
        if self.current is None:return None
        if text not in FOLLOWUPS:
            self.clear()
            return None
        if self.turn>=1:
            self.clear()
            return {"answer":"この資料から確実に紹介できる追加情報はここまで。ほかに知りたいことはある？",
                    "route":"WIKIPEDIA_EVIDENCE_EXHAUSTED","source":None,
                    "verified":False,"train_ready":False}
        parts=[p.strip() for p in re.split(r"[。\n]",self.current.get("extract","")) if p.strip()]
        self.turn+=1
        # First sentence was already displayed in initial grounded response.
        for sentence in parts[1:]:
            if 15<=len(sentence)<=180:
                return {"answer":"同じWikipedia記事には、"+sentence.rstrip("。")+"。とも書かれている。",
                        "route":"WIKIPEDIA_CONTEXT_FOLLOWUP",
                        "source":self.current["url"],
                        "verified":False,"train_ready":False}
        self.clear()
        return {"answer":"この資料からは、それ以上の詳しい説明を確認できない。何を知りたい？",
                "route":"WIKIPEDIA_EVIDENCE_EXHAUSTED",
                "source":None,"verified":False,"train_ready":False}
