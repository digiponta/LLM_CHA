"""v0.5.29 read-only Wikipedia two-hop evidence diagnostic.

Fetches the resolved article and up to four same-wiki linked articles. Does
not alter replies, memory, truth state or model weights. A chain is a syntactic
hypothesis, not verified physics.
"""
import re
from urllib.parse import quote
from wikipedia_acquisition_v0517 import _request
from wiki_multihop_causal_v0528 import compose, edge

def probe(wiki,question,fetch=None,max_articles=4):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_CONTEXT","visited":[]}
    title=wiki.get("title")
    if not isinstance(title,str) or not title or not 0<=max_articles<=5:
        return {"status":"NO_CONTEXT","visited":[]}
    visited=[]; evidence=[]
    try:
        links=_request({"action":"query","prop":"links","titles":title,"pllimit":40,
            "format":"json","formatversion":2},fetch)
        pages=links.get("query",{}).get("pages",[])
        if not pages or pages[0].get("title")!=title:
            return {"status":"NO_RELATED_PAGES","visited":[]}
        titles=[title]+sorted({x.get("title","") for x in pages[0].get("links",[])
            if isinstance(x.get("title"),str) and ":" not in x["title"] and x["title"]!=title},
            key=lambda x:(-sum(v in x for v in ("ジョセフソン","量子","磁束","超伝導")),x))[:max_articles]
        for candidate in titles:
            obj=_request({"action":"query","prop":"extracts","titles":candidate,
                "redirects":1,"explaintext":1,"exchars":3000,
                "format":"json","formatversion":2},fetch)
            rows=obj.get("query",{}).get("pages",[])
            if not rows or rows[0].get("missing"):continue
            actual=rows[0].get("title")
            body=rows[0].get("extract","")
            if not isinstance(actual,str) or not isinstance(body,str) or not body:continue
            visited.append(actual)
            source="https://ja.wikipedia.org/wiki/"+quote(actual.replace(" ","_"))
            for sentence in re.split(r"[。\n]",body):
                sentence=sentence.strip()
                if 12<=len(sentence)<=240 and edge(sentence,source):
                    evidence.append({"sentence":sentence,"source":source})
                    if len(evidence)>=40:break
        result=compose(question,evidence)
        result["visited"]=visited
        result["edge_candidates"]=len(evidence)
        result["diagnostic_only"]=True
        result["verified"]=False
        result["train_ready"]=False
        return result
    except (OSError,ValueError,KeyError,TypeError,TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","reason":type(exc).__name__,"visited":visited,
                "diagnostic_only":True}
