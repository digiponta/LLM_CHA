"""v0.5.36 read-only multi-article typed proposition/evidence comparison.

No causal relation is inferred from common entities, co-occurrence, or
similarity. Only explicit relation candidates are evaluated separately.
"""
import re
from urllib.parse import quote
from wikipedia_acquisition_v0517 import _request
from wiki_proposition_comparison_v0537 import collect, compare_all
from wiki_relation_alignment_v0535 import align
from wiki_extraction_coverage_v0538 import diagnose_body

def analyze(wiki,question,fetch=None,max_articles=4):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND" or not isinstance(wiki.get("title"),str) or not 0<=max_articles<=5:
        return {"status":"NO_CONTEXT","articles":[]}
    root=wiki["title"]; articles=[];propositions=[];relations=[]
    try:
        links=_request({"action":"query","prop":"links","titles":root,"pllimit":40,"format":"json","formatversion":2},fetch)
        pages=links.get("query",{}).get("pages",[])
        if not pages or pages[0].get("title")!=root:
            return {"status":"NO_RELATED_PAGES","articles":[]}
        titles=[root]+sorted({e["title"] for e in pages[0].get("links",[]) if isinstance(e.get("title"),str)
             and ":" not in e["title"] and e["title"]!=root},key=lambda s:(-sum(k in s for k in ("ジョセフソン","量子","磁束","超伝導")),s))[:max_articles]
        for title in titles:
            obj=_request({"action":"query","prop":"extracts","titles":title,"redirects":1,
                "explaintext":1,"exchars":3000,"format":"json","formatversion":2},fetch)
            entries=obj.get("query",{}).get("pages",[])
            if not entries or entries[0].get("missing"):continue
            p=entries[0];name=p.get("title");body=p.get("extract")
            if not isinstance(name,str) or not isinstance(body,str):continue
            url="https://ja.wikipedia.org/wiki/"+quote(name.replace(" ","_"))
            article_props=0;article_relations=0
            for raw in re.split(r"[。\n]",body):
                sentence=raw.strip()
                if not 12<=len(sentence)<=240:continue
                sentence+="。"
                atoms=collect(sentence,url)
                propositions.extend(atoms[:max(0,50-len(propositions))])
                article_props+=len(atoms)
                result=align(question,sentence,url)
                relations.extend(result.get("candidates",[])[:max(0,30-len(relations))])
                article_relations+=len(result.get("candidates",[]))
            articles.append({"title":name,"source":url,"typed_count":article_props,"relation_count":article_relations,
                             "coverage":diagnose_body(body,url,sample_limit=3)})
        # Identity of subject + predicate + object is a duplicate proposition,
        # not proof of a causal link or independent verification.
        keys={};duplicates=[]
        for p in propositions:
            key=(p["subject"],p["predicate"],p["object"])
            if key in keys:
                duplicates.append({"key":list(key),"sources":sorted({keys[key],p["source"]})})
            else:keys[key]=p["source"]
        return {"status":"EVIDENCE_COLLECTED","articles":articles,
            "propositions":propositions,"aligned_candidates":[r for r in relations if r.get("aligned")],
            "rejected_candidates":[r for r in relations if not r.get("aligned")],
            "duplicate_propositions":duplicates,
            "comparison":compare_all(propositions),
            "causal_answer_approved":False,"diagnostic_only":True,
            "verified":False,"train_ready":False,"promoted":False}
    except (OSError,ValueError,KeyError,TypeError,TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","reason":type(exc).__name__,"articles":articles,
                "causal_answer_approved":False,"diagnostic_only":True}
