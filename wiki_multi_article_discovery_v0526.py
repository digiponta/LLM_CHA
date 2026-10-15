"""v0.5.26 bounded multi-article Wikipedia evidence discovery.

Related articles are candidates, NOT automatically evidence for the subject.
Strictly require the original concept (SQUID or title) in the selected sentence.
No persistent writes, training or factual verification.
"""
import re
from urllib.parse import quote
from wikipedia_acquisition_v0517 import _request
from wiki_evidence_expansion_v0521 import intent
from wiki_answerability_gate_v0522 import evaluate
from wiki_polarity_gate_v0523 import check
from wiki_causal_direction_v0527 import check_direction
from wiki_proposition_alignment_v0524 import align

def discover(wiki,question,fetch=None,max_articles=5):
    kind=intent(question)
    if kind=="OTHER":return {"status":"NOT_APPLICABLE","intent":kind}
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_CONTEXT","intent":kind}
    title=wiki.get("title","")
    if not isinstance(title,str) or not title or not 1<=max_articles<=8:
        return {"status":"NO_CONTEXT","intent":kind}
    try:
        links=_request({"action":"query","prop":"links","titles":title,"pllimit":40,
            "format":"json","formatversion":2},fetch)
        pages=links.get("query",{}).get("pages",[])
        if not pages or pages[0].get("title")!=title:return {"status":"NO_RELATED_PAGES","intent":kind}
        titles=[x.get("title","") for x in pages[0].get("links",[])
                if isinstance(x.get("title"),str) and ":" not in x["title"]]
        # Keyword priors only order exploration; never establish truth.
        preferences=("ジョセフソン","磁束","超伝導","量子","脳磁","磁気")
        titles=sorted(set(titles),key=lambda t:(-sum(x in t for x in preferences),t))
        visited=[]
        for candidate in titles[:max_articles]:
            data=_request({"action":"query","prop":"extracts","titles":candidate,
                "redirects":1,"explaintext":1,"exchars":3000,
                "format":"json","formatversion":2},fetch)
            rows=data.get("query",{}).get("pages",[])
            if not rows or rows[0].get("missing"):continue
            page=rows[0]
            actual=page.get("title","")
            if not isinstance(actual,str) or not actual:continue
            visited.append(actual)
            extract=page.get("extract","")
            if not isinstance(extract,str):continue
            for sentence in (x.strip() for x in re.split(r"[。\n]",extract)):
                if not 15<=len(sentence)<=240:continue
                # Related physical principles do not necessarily explain SQUID.
                if not any(token in sentence for token in ("SQUID","超伝導量子干渉計")):continue
                if not evaluate(sentence,kind,question)["answerable"]:continue
                if not check(question,sentence,kind)["supported"]:continue
                if not align(question,sentence,kind,subject="SQUID")["aligned"]:continue
                if not check_direction(question,sentence,kind)["supported"]:continue
                return {"status":"FOUND","intent":kind,"title":actual,
                    "sentence":sentence,"source":"https://ja.wikipedia.org/wiki/"+quote(actual.replace(" ","_")),
                    "visited":visited,"truth_state":"EXTERNAL_UNVERIFIED",
                    "verified":False,"train_ready":False,
                    "quality_gate":"MULTI_ARTICLE_CONSERVATIVE_ALIGNMENT"}
        return {"status":"NO_ANSWERABLE_RELATED_EVIDENCE","intent":kind,"visited":visited}
    except (OSError,ValueError,KeyError,TypeError,TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","intent":kind,"error":type(exc).__name__}
