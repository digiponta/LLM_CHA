"""v0.5.60 source-bounded 'more details' from the SAME Wikipedia article.

Fetch a longer extract only after short cached evidence is exhausted.
Never switch articles, claim verification, or train from retrieved content.
"""
import re
from wikipedia_acquisition_v0517 import _request
from wiki_persona_multiturn_v0520 import FOLLOWUPS

def more(wiki,question,persona="nagato",fetch=None):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_CONTEXT"}
    if not isinstance(question,str) or question.strip().rstrip("。！？!? ") not in FOLLOWUPS:
        return {"status":"NOT_APPLICABLE"}
    title=wiki.get("title","")
    url=wiki.get("url","")
    if not title or len(title)>100 or not isinstance(url,str) or not url.startswith("https://ja.wikipedia.org/wiki/"):
        return {"status":"INVALID_SOURCE"}
    try:
        response=_request({"action":"query","prop":"extracts","titles":title,"redirects":1,
                          "explaintext":1,"exchars":4000,"format":"json","formatversion":2},fetch)
        pages=response.get("query",{}).get("pages",[])
        if not pages or pages[0].get("missing") or pages[0].get("title")!=title:
            return {"status":"SOURCE_MISMATCH"}
        extended=pages[0].get("extract","")
        if not isinstance(extended,str) or not extended.strip():
            return {"status":"NO_EVIDENCE"}
        original=wiki.get("extract","")
        # The longer extract must reproduce the original introduction.
        if not extended.startswith(original):
            return {"status":"SOURCE_MISMATCH"}
        remainder=extended[len(original):]
        # The original 900-char extract may end mid-sentence: discard that
        # partial sentence, never reconstruct ungrounded spans.
        cut=remainder.find("。")
        if original and not original.endswith(("。","\n")):
            remainder=remainder[cut+1:] if cut>=0 else ""
        sentences=[x.strip() for x in re.split(r"[。\n]",remainder)
                   if 20<=len(x.strip())<=220]
        if not sentences:return {"status":"NO_NEW_SENTENCE"}
        fact=sentences[0]
        if fact not in extended:return {"status":"NO_EVIDENCE"}
        answer=("Wikipediaには、"+fact+"。とある。" if persona=="nagato"
                else "Wikipediaには、"+fact+"。と記載されています。")
        return {"status":"FOUND","answer":answer,
                "source":url,"title":title,
                "route":"PERSONA_WIKIPEDIA_EXTENDED_MORE",
                "quality_gate":"SAME_ARTICLE_EXACT_SPAN",
                "truth_state":"EXTERNAL_UNVERIFIED","verified":False,
                "train_ready":False,"auto_promote":False}
    except (OSError,ValueError,TypeError,KeyError,TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","error":type(exc).__name__}
