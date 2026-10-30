"""Collect public Wikipedia excerpts for *unreviewed* source-grounded evaluation.

All retrieved text is external and unverified. No labels are inferred or approved.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode,quote
from urllib.request import Request,urlopen

SEEDS=[
 ("宇宙","宇宙とは"),
 ("ビッグバン","ビッグバンはいつ起きたのか"),
 ("ダークエネルギー","ダークエネルギーとは"),
 ("スファレライト","スファレライトの化学組成は"),
 ("水","水の化学組成は"),
 ("中央処理装置","中央処理装置とは"),
 ("量子力学","量子力学とは"),
 ("光電効果","光電効果とは"),
]
API="https://ja.wikipedia.org/w/api.php"

def fetch_extract(title,timeout=20,opener=urlopen):
    params={"action":"query","prop":"extracts","explaintext":"1","exsectionformat":"plain",
            "redirects":"1","titles":title,"format":"json","formatversion":"2"}
    req=Request(API+"?"+urlencode(params),headers={"User-Agent":"LLM-CHA-evidence-evaluation/0.13.58.82.60 (research; no automated labels)"})
    with opener(req,timeout=timeout) as response:
        data=json.loads(response.read().decode("utf-8"))
    pages=data.get("query",{}).get("pages",[])
    if not pages or pages[0].get("missing") or not pages[0].get("extract","").strip():
        raise ValueError("MISSING_ARTICLE_OR_EXTRACT")
    page=pages[0]
    return {"page_id":page.get("pageid"),"title":page.get("title",title),
            "url":"https://ja.wikipedia.org/wiki/"+quote(page.get("title",title).replace(" ","_")),
            "excerpt":page["extract"]}

def collect(seeds,fetch=fetch_extract,when=None):
    stamp=when or datetime.datetime.now(datetime.timezone.utc).isoformat()
    cases=[];failures=[]
    for title,question in seeds:
        try:
            source=fetch(title)
            excerpt=source["excerpt"][:900]
            digest=hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
            cases.append({"id":"wiki-"+str(source.get("page_id") or title),
                          "question":question,
                          "evidence":{"status":"EVIDENCE","topic":source["title"],
                            "excerpt":excerpt,"url":source["url"],"trust":"EXTERNAL_UNVERIFIED"},
                          "source":{"page_id":source.get("page_id"),"title":source["title"],
                            "retrieved_at_utc":stamp,"excerpt_sha256":digest,
                            "excerpt_chars":len(excerpt),"truncated":len(source["excerpt"])>900},
                          "review":{"status":"PENDING_HUMAN_REVIEW","source_independent":False,
                            "answerable":None,"required_substring":None,"reviewer_note":None}})
        except (ValueError,OSError,TimeoutError,json.JSONDecodeError) as exc:
            failures.append({"title":title,"error":type(exc).__name__,"detail":str(exc)[:160]})
    return {"format":"real_evidence_review_v013588260","collection_status":"UNREVIEWED",
            "created_utc":stamp,"cases":cases,"failures":failures}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="data/wiki_evidence_review_v013588260.json")
    args=p.parse_args()
    result=collect(SEEDS)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["collection_status"],"collected":len(result["cases"]),
                      "failures":len(result["failures"]),"path":str(path)},ensure_ascii=False))
if __name__=="__main__":main()
