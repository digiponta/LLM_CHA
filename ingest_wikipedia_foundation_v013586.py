"""v0.13.58.6: opt-in Wikipedia article ingestion for Japanese foundation candidates.

Requires a meaningful --user-agent (with contact URL/email), --run and explicit
titles file. One Action API request per article, serial with delay.
Source-level train/eval split is deterministic by article ID, never by sentence.
No training, automatic approval, or implied data-license clearance.
"""
import argparse,hashlib,json,re,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path

API="https://ja.wikipedia.org/w/api.php"
def digest(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def article_partition(pageid,salt="foundation-v013586",eval_percent=20):
    if not 1<=eval_percent<=50:raise ValueError("bad evaluation percentage")
    value=int(digest(f"{salt}:{pageid}")[:12],16)%100
    return "eval" if value<eval_percent else "train"
def sentences(text,min_chars=18,max_chars=350):
    if min_chars<1 or max_chars<min_chars:raise ValueError("bad lengths")
    # Leave citations/source markup in evidence metadata, not in the dataset.
    text=re.sub(r"\[[0-9０-９]+\]","",text)
    text=re.sub(r"\s+"," ",text)
    parts=re.split(r"(?<=[。！？])\s*",text)
    return [s.strip() for s in parts if min_chars<=len(s.strip())<=max_chars
            and ("。" in s or "！" in s or "？" in s)]
def read_titles(path):
    rows=[s.strip() for s in path.read_text(encoding="utf-8-sig").splitlines()
          if s.strip() and not s.lstrip().startswith("#")]
    if not rows or len(rows)!=len(set(rows)):raise ValueError("empty/duplicate article titles")
    if len(rows)>100:raise ValueError("at most 100 titles per run")
    return rows
def query_article(title,user_agent,timeout=30):
    params={"action":"query","format":"json","formatversion":"2","prop":"extracts|info|revisions",
      "inprop":"url","explaintext":"1","rvprop":"ids|timestamp","titles":title,"redirects":"1","maxlag":"5"}
    url=API+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":user_agent,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        payload=json.load(response)
    if "error" in payload:raise ValueError(str(payload["error"]))
    pages=payload.get("query",{}).get("pages",[])
    if len(pages)!=1:raise ValueError("unexpected page count")
    p=pages[0]
    if p.get("missing") or p.get("ns")!=0:return None
    if not p.get("extract") or not p.get("pageid"):return None
    rev=p.get("revisions") or [{}]
    return {"pageid":p["pageid"],"title":p["title"],"url":p.get("fullurl"),
       "revision_id":rev[0].get("revid"),"revision_timestamp":rev[0].get("timestamp"),
       "extract":p["extract"]}
def ingest(titles,fetch,eval_percent=20,min_chars=18):
    train=[];evaluation=[];manifest=[];seen=set()
    for title in titles:
        page=fetch(title)
        if page is None:
            manifest.append({"requested_title":title,"status":"MISSING_OR_EMPTY"});continue
        pid=page["pageid"]
        if pid in seen:continue
        seen.add(pid)
        partition=article_partition(pid,eval_percent=eval_percent)
        lines=list(dict.fromkeys(sentences(page["extract"],min_chars=min_chars)))
        meta={"requested_title":title,"title":page["title"],"pageid":pid,
              "url":page["url"],"revision_id":page["revision_id"],
              "revision_timestamp":page["revision_timestamp"],"partition":partition,
              "sentence_count":len(lines),"source_sha256":digest(page["extract"])}
        manifest.append(meta)
        for i,s in enumerate(lines):
            item={"pageid":pid,"title":page["title"],"revision_id":page["revision_id"],
                  "source_url":page["url"],"sentence_index":i,"text":s}
            (evaluation if partition=="eval" else train).append(item)
    return train,evaluation,manifest
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--titles",type=Path,default=Path("data/foundation_wikipedia_titles_v013586.txt"))
    p.add_argument("--user-agent",required=True,help="e.g. LLM_CHA/0.13.58.6 (https://github.com/digiponta/LLM_CHA)")
    p.add_argument("--output-dir",type=Path,default=Path("results/wikipedia_foundation_v013586"))
    p.add_argument("--eval-percent",type=int,default=20)
    p.add_argument("--delay",type=float,default=1.0)
    p.add_argument("--min-chars",type=int,default=18)
    p.add_argument("--run",action="store_true",help="make API requests; preflight otherwise")
    a=p.parse_args()
    if not a.titles.is_file():p.error("missing titles file")
    if "http" not in a.user_agent and "@" not in a.user_agent:p.error("identify client with contact URL or email")
    if a.delay<0.5:p.error("delay must be >=0.5 seconds")
    if not 1<=a.eval_percent<=50:p.error("bad eval-percent")
    titles=read_titles(a.titles)
    outputs=[a.output_dir/name for name in ("train.txt","train_records.jsonl",
              "eval_records.jsonl","manifest.json")]
    if any(q.exists() for q in outputs):p.error("output exists; refusing overwrite")
    print(json.dumps({"version":"v0.13.58.6","preflight":"PASS",
                      "article_titles":len(titles),"run":a.run},ensure_ascii=False))
    if not a.run:return
    def fetch(title):
        try:return query_article(title,a.user_agent)
        except (urllib.error.HTTPError,urllib.error.URLError) as exc:
            raise RuntimeError(f"fetch failed for {title}: {exc}") from exc
    def paced(title):
        item=fetch(title)
        time.sleep(a.delay)
        return item
    train,ev,manifest=ingest(titles,paced,a.eval_percent,a.min_chars)
    # Require actual article-disjoint evaluation before writing anything.
    train_ids={x["pageid"] for x in train};eval_ids={x["pageid"] for x in ev}
    if not train_ids or not eval_ids or train_ids & eval_ids:
        p.error("train/eval article disjointness or nonempty partitions failed; use more articles")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    with outputs[0].open("x",encoding="utf-8",newline="\n") as f:
        for row in train:f.write(row["text"]+"\n")
    for path,rows in [(outputs[1],train),(outputs[2],ev)]:
        with path.open("x",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    report={"version":"v0.13.58.6","status":"ACQUIRED_UNREVIEWED",
      "requested":len(titles),"articles_train":len(train_ids),"articles_eval":len(eval_ids),
      "sentences_train":len(train),"sentences_eval":len(ev),"source_manifest":manifest,
      "license_note":"Wikipedia text is generally CC BY-SA; verify per-page terms, attribution and share-alike obligations before redistribution.",
      "license_reviewed":False,"human_quality_reviewed":False,
      "historical_model_exposure_excluded":False,"training_approved":False,
      "eval_is_source_separated_not_model_independent":True,
      "client_user_agent":a.user_agent}
    with outputs[3].open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ("status","articles_train","articles_eval","sentences_train","sentences_eval","training_approved")},ensure_ascii=False))
    print("manifest:",outputs[3])
if __name__=="__main__":main()
