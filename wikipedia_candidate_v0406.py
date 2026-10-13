"""LLM_CHA v0.4.6: read-only Wikipedia search candidate retrieval.

Does NOT write to Semantic Memory, Truth Gate, or training queues.
Python standard library only. Search snippets are UNVERIFIED and not definitions.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html import unescape
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

API="https://ja.wikipedia.org/w/rest.php/v1/search/page"
USER_AGENT="LLM_CHA-WikipediaResearch/0.4.6 (https://github.com/digiponta/LLM_CHA; research tool)"
MAX_RESPONSE=512_000

def clean_snippet(value):
    if not isinstance(value,str):
        return ""
    value=re.sub(r"<[^>]*>","",value)
    return unescape(value).strip()[:500]

def parse_results(data, concept, timestamp):
    if not isinstance(data,dict) or not isinstance(data.get("pages"),list):
        raise ValueError("invalid Wikipedia search response")
    candidates=[]
    for page in data["pages"][:5]:
        if not isinstance(page,dict):continue
        title=page.get("title")
        if not isinstance(title,str) or not title.strip():continue
        title=title.strip()
        candidates.append({
            "concept":concept,"title":title,
            "description":clean_snippet(page.get("description")),
            "search_excerpt":clean_snippet(page.get("excerpt")),
            "url":"https://ja.wikipedia.org/wiki/"+quote(title.replace(" ","_"),safe=""),
            "source":"WIKIPEDIA_SEARCH_RESULT",
            "factual_truth":"UNVERIFIED","review_state":"PENDING_REVIEW",
            "retrieved_at_utc":timestamp,
            "is_full_article":False,"eligible_for_training":False,
        })
    return {"version":"v0.4.6","concept":concept,"source":"Wikipedia (ja)",
            "query_url":API+"?"+urlencode({"q":concept,"limit":5}),
            "candidates":candidates,"candidate_count":len(candidates),
            "truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False}

def retrieve(concept, timeout=10):
    concept=concept.strip()
    if not concept or len(concept)>100 or any(x in concept for x in "\r\n\0"):
        raise ValueError("invalid concept")
    if not (1<=timeout<=30):raise ValueError("timeout must be 1..30 seconds")
    url=API+"?"+urlencode({"q":concept,"limit":5})
    req=Request(url,headers={"User-Agent":USER_AGENT,
                             "Accept":"application/json"})
    with urlopen(req,timeout=timeout) as response:
        if getattr(response,"status",200)!=200:raise ValueError("Wikipedia HTTP error")
        raw=response.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE:raise ValueError("Wikipedia response too large")
    data=json.loads(raw.decode("utf-8"))
    timestamp=datetime.now(timezone.utc).isoformat()
    return parse_results(data,concept,timestamp)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("concept",help="Unknown Japanese concept to research")
    p.add_argument("--timeout",type=int,default=10)
    p.add_argument("--report",default=None,help="Optional output JSON path (not Semantic Memory)")
    args=p.parse_args()
    try:
        result=retrieve(args.concept,args.timeout)
    except (ValueError,UnicodeError,URLError,HTTPError,TimeoutError,json.JSONDecodeError) as exc:
        p.exit(1,f"Wikipedia retrieval failed: {type(exc).__name__}: {exc}\n")
    serialized=json.dumps(result,ensure_ascii=False,indent=2)
    if args.report:
        from pathlib import Path
        out=Path(args.report)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(serialized,encoding="utf-8")
    print(serialized)
if __name__=="__main__":main()
