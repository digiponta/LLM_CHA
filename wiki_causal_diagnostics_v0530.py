"""v0.5.30: read-only sentence-level causal extraction diagnostics.

Counts extraction failures without interpreting rejected sentences as evidence.
Reports only bounded samples and no automatic memory/training modifications.
"""
import re
from collections import Counter
from urllib.parse import quote
from wikipedia_acquisition_v0517 import _request
from wiki_multihop_causal_v0528 import edge, MARKERS, TERMS
from wiki_proposition_decomposition_v0531 import decompose

def diagnose_extract(body,source,sample_limit=3):
    counts=Counter()
    samples=[]
    counts["decomposed_propositions"]=0
    for raw in re.split(r"[。\n]",body):
        sentence=raw.strip()
        if not sentence:continue
        counts["sentences"]+=1
        counts["decomposed_propositions"]+=len(decompose(sentence,source))
        if not 12<=len(sentence)<=240:
            reason="LENGTH_OUT_OF_RANGE"
        elif not any(m in sentence for m in MARKERS):
            reason="NO_CAUSAL_MARKER"
        elif not any(any(form in sentence for form in forms) for forms in TERMS.values()):
            reason="NO_RECOGNIZED_CONCEPT"
        elif edge(sentence,source) is None:
            reason="INVALID_OR_AMBIGUOUS_EDGE"
        else:
            reason="EDGE_EXTRACTED"
        counts[reason]+=1
        if len(samples)<sample_limit and reason!="EDGE_EXTRACTED":
            samples.append({"reason":reason,"excerpt":sentence[:120]})
    return {"counts":dict(counts),"samples":samples}

def diagnose(wiki,fetch=None,max_articles=4,sample_limit=3):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_CONTEXT"}
    title=wiki.get("title")
    if not isinstance(title,str) or not title or not 0<=max_articles<=5:
        return {"status":"NO_CONTEXT"}
    totals=Counter();articles=[];samples=[]
    try:
        response=_request({"action":"query","prop":"links","titles":title,"pllimit":40,
            "format":"json","formatversion":2},fetch)
        pages=response.get("query",{}).get("pages",[])
        if not pages or pages[0].get("title")!=title:
            return {"status":"NO_RELATED_PAGES","articles":[]}
        links=[x.get("title","") for x in pages[0].get("links",[])
               if isinstance(x.get("title"),str) and ":" not in x["title"] and x["title"]!=title]
        names=[title]+sorted(set(links),key=lambda x:(-sum(t in x for t in ("ジョセフソン","量子","磁束","超伝導")),x))[:max_articles]
        for name in names:
            response=_request({"action":"query","prop":"extracts","titles":name,
                "redirects":1,"explaintext":1,"exchars":3000,
                "format":"json","formatversion":2},fetch)
            rows=response.get("query",{}).get("pages",[])
            if not rows or rows[0].get("missing"):continue
            actual=rows[0].get("title","")
            body=rows[0].get("extract","")
            if not isinstance(actual,str) or not actual or not isinstance(body,str):continue
            item=diagnose_extract(body,"https://ja.wikipedia.org/wiki/"+quote(actual.replace(" ","_")),sample_limit)
            articles.append({"title":actual,"counts":item["counts"]})
            totals.update(item["counts"])
            for example in item["samples"]:
                if len(samples)<sample_limit:
                    samples.append({"article":actual,**example})
        return {"status":"DIAGNOSTIC_COMPLETE","articles":articles,"totals":dict(totals),
                "samples":samples,"diagnostic_only":True,"verified":False,"train_ready":False}
    except (OSError,ValueError,KeyError,TypeError,TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","reason":type(exc).__name__,
                "articles":articles,"diagnostic_only":True}
