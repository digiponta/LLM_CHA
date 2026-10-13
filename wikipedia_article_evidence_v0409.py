"""v0.4.9: read-only Wikipedia article-lead evidence, revision-bound.

Fetches current Japanese Wikipedia page extract via MediaWiki Action API.
Not a truth verification, not an article citation check, and never learning.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from external_candidate_store_v0407 import _store,_atomic_write

API="https://ja.wikipedia.org/w/api.php"
USER_AGENT="LLM_CHA-ArticleEvidence/0.4.9 (https://github.com/digiponta/LLM_CHA)"
MAX_RESPONSE=512_000
MAX_EXTRACT=6000

def parse_article(payload, candidate, observed_at):
    pages=payload.get("query",{}).get("pages")
    if not isinstance(pages,list) or len(pages)!=1:
        raise ValueError("invalid page response")
    p=pages[0]
    if not isinstance(p,dict) or p.get("missing") is True or p.get("invalid") is True:
        raise ValueError("article missing")
    pageid=p.get("pageid"); revid=p.get("revisions",[{}])[0].get("revid") if isinstance(p.get("revisions"),list) and p["revisions"] else None
    title=p.get("title"); extract=p.get("extract")
    if (not isinstance(pageid,int) or pageid<=0 or not isinstance(revid,int) or revid<=0
        or not isinstance(title,str) or not isinstance(extract,str) or not extract.strip()):
        raise ValueError("page id, revision or extract missing")
    if len(extract)>MAX_EXTRACT:extract=extract[:MAX_EXTRACT]
    # The page must resolve to the same title, no silent redirect onto another topic.
    if title.replace("_"," ").strip()!=candidate["title"].replace("_"," ").strip():
        raise ValueError("article title mismatch or redirect")
    content_sha=hashlib.sha256(extract.encode("utf-8")).hexdigest()
    return {"version":"v0.4.9","candidate_id":candidate["id"],
            "candidate_content_sha256":candidate["content_sha256"],
            "concept":candidate["concept"],"article_title":title,
            "article_url":candidate["url"],"pageid":pageid,"revid":revid,
            "observed_at_utc":observed_at,"extract_sha256":content_sha,
            "lead_extract":extract,"extract_kind":"PLAIN_TEXT_INTRO",
            "is_full_article":False,"revision_content_verified":False,
            "factual_truth":"UNVERIFIED","human_article_reviewed":False,
            "eligible_for_training":False,"semantic_memory_writes":0,
            "truth_promotions":0}

def fetch_article(candidate,timeout=10):
    if not 1<=timeout<=30:raise ValueError("invalid timeout")
    params={"action":"query","format":"json","formatversion":2,
            "prop":"extracts|revisions","exintro":1,"explaintext":1,
            "rvprop":"ids","titles":candidate["title"],"redirects":0}
    url=API+"?"+urlencode(params)
    req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urlopen(req,timeout=timeout) as resp:
        if getattr(resp,"status",200)!=200:raise ValueError("HTTP response error")
        data=resp.read(MAX_RESPONSE+1)
        if len(data)>MAX_RESPONSE:raise ValueError("oversized response")
    return parse_article(json.loads(data.decode("utf-8")),candidate,
                         datetime.now(timezone.utc).isoformat())

def inspect(store_path,id,sha256,timeout=10):
    path=Path(store_path)
    if not path.is_file():raise ValueError("candidate store missing")
    db=_store(path)
    rows=[x for x in db["records"] if x.get("id")==id]
    if len(rows)!=1:raise ValueError("candidate not found")
    candidate=rows[0]
    if candidate.get("content_sha256")!=sha256:raise ValueError("candidate SHA mismatch")
    if candidate.get("source")!="WIKIPEDIA_SEARCH_RESULT" or candidate.get("factual_truth")!="UNVERIFIED" or candidate.get("eligible_for_training") is not False:
        raise ValueError("candidate invalid")
    return fetch_article(candidate,timeout)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--store",default="results/external_candidate_store_v0407.json")
    p.add_argument("--id",required=True)
    p.add_argument("--sha256",required=True)
    p.add_argument("--timeout",type=int,default=10)
    p.add_argument("--report",default=None,help="Optional isolated evidence JSON report")
    a=p.parse_args()
    try:
        result=inspect(a.store,a.id,a.sha256,a.timeout)
        if a.report:_atomic_write(a.report,result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,TypeError,KeyError,IndexError,UnicodeError,json.JSONDecodeError) as e:
        p.exit(1,f"Article evidence failed: {type(e).__name__}: {e}\n")
if __name__=="__main__":main()
