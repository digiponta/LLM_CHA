"""v0.8.0.11: conservative Wikipedia ambiguity selection session."""
from wikipedia_acquisition_v0517 import lookup

class PendingWikiTopic:
    def __init__(self):
        self.topic=None
        self.candidates=[]
    def clear(self):
        self.topic=None
        self.candidates=[]
    def start(self,topic,result):
        self.clear()
        if result.get("status")!="AMBIGUOUS":return False
        candidates=[c for c in result.get("candidates",[]) if isinstance(c,str)]
        self.topic=topic
        self.candidates=list(dict.fromkeys(candidates))[:5]
        return bool(self.candidates)
    def message(self):
        if not self.candidates:return "候補が見つかりませんでした。"
        return "{}の候補が複数あります。番号で選択してください: {}".format(
            self.topic," / ".join("{}:{}".format(i,t) for i,t in enumerate(self.candidates,1)))
    def selection(self,text):
        q=(text or "").strip()
        if not self.topic:return None
        if q in ("キャンセル","/wiki-cancel"):
            self.clear()
            return {"status":"CANCELLED"}
        if q in ("もう少し詳しく","もっと詳しく","詳しく教えて"):
            return {"status":"PENDING","message":self.message()}
        if q.isdecimal():
            n=int(q)
            if 1<=n<=len(self.candidates):
                chosen=self.candidates[n-1]
                return {"status":"SELECTED","title":chosen,"topic":self.topic}
            return {"status":"INVALID_SELECTION","message":self.message()}
        self.clear()
        return None
