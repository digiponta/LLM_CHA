"""v0.5.62 repeated Wikipedia follow-ups with distinct source-backed evidence."""
import re
from wikipedia_acquisition_v0517 import _request
from wiki_persona_multiturn_v0520 import FOLLOWUPS

def readable_evidence(sentence):
    """Reject equation markup, captions, fragments and text without prose."""
    if not isinstance(sentence,str):return False
    if any(token in sentence for token in ("{\\displaystyle", "\\rangle", "\\langle", "\\frac", "\\sum", "\\psi")):
        return False
    if re.search(r"[{}\\]|[=<>]",sentence):return False
    japanese=len(re.findall(r"[ぁ-んァ-ヶ一-龯]",sentence))
    if japanese<12 or len(sentence)<25:return False
    if not re.search(r"(である|です|ます|れる|する|した|となる|を表|により|において|という|と呼ばれ|がある|であり|できる|される)",sentence):
        return False
    return True

class EvidenceSession:
    def __init__(self):
        self.identity=None
        self.seen=set()
    def reset(self):
        self.identity=None
        self.seen.clear()
    def next(self,wiki,question,persona="nagato",fetch=None):
        if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
            self.reset()
            return {"status":"NO_CONTEXT"}
        if question.strip().rstrip("。！？!? ") not in FOLLOWUPS:
            return {"status":"NOT_APPLICABLE"}
        title,url=wiki.get("title",""),wiki.get("url","")
        if not isinstance(title,str) or not title or len(title)>100 or not isinstance(url,str) or not url.startswith("https://ja.wikipedia.org/wiki/"):
            return {"status":"INVALID_SOURCE"}
        identity=(title,url)
        if identity!=self.identity:
            self.identity=identity
            self.seen=set()
        try:
            data=_request({"action":"query","prop":"extracts","titles":title,"redirects":1,
                           "explaintext":1,"exchars":4000,"format":"json","formatversion":2},fetch)
            pages=data.get("query",{}).get("pages",[])
            if not pages or pages[0].get("missing") or pages[0].get("title")!=title:
                return {"status":"SOURCE_MISMATCH"}
            extended=pages[0].get("extract","")
            original=wiki.get("extract","")
            if not isinstance(extended,str) or not isinstance(original,str) or not extended.startswith(original):
                return {"status":"SOURCE_MISMATCH"}
            remainder=extended[len(original):]
            if original and not original.endswith(("。","\n")):
                cut=remainder.find("。")
                remainder=remainder[cut+1:] if cut>=0 else ""
            sentences=[x.strip() for x in re.split(r"[。\n]",remainder)
                       if 20<=len(x.strip())<=220]
            for sentence in sentences:
                if sentence in self.seen:continue
                if not readable_evidence(sentence):continue
                if sentence not in extended:continue
                self.seen.add(sentence)
                answer=("Wikipediaには、"+sentence+"。とある。" if persona=="nagato"
                        else "Wikipediaには、"+sentence+"。と記載されています。")
                return {"status":"FOUND","answer":answer,"source":url,"title":title,
                        "route":"PERSONA_WIKIPEDIA_EVIDENCE_SESSION",
                        "quality_gate":"SAME_ARTICLE_UNSEEN_EXACT_SPAN",
                        "truth_state":"EXTERNAL_UNVERIFIED","verified":False,
                        "train_ready":False,"auto_promote":False}
            return {"status":"EVIDENCE_EXHAUSTED","source":url,
                    "verified":False,"train_ready":False}
        except (OSError,ValueError,TypeError,KeyError,TimeoutError) as exc:
            return {"status":"LOOKUP_FAILED","reason":type(exc).__name__}
