"""v0.13.58.9: curl.exe transport and cache for Wikipedia REST Wikitext.

Windows curl.exe succeeded when Python urllib returned 503. Use curl as a
selectable transport; preserve source JSON locally, allow resume, and reject
non-200 responses. Requires prior v0.13.58.8 ingester, mwparserfromhell.
"""
import argparse,hashlib,json,subprocess,sys,time,urllib.parse
from pathlib import Path
import ingest_wikipedia_wikitext_v013588 as wiki

def curl_article(title,user_agent,cache_dir,timeout=30):
    key=hashlib.sha256(title.encode("utf-8")).hexdigest()
    path=cache_dir/(key+".json")
    if path.exists():
        obj=json.loads(path.read_text(encoding="utf-8"))
        if obj.get("requested_title")!=title:raise ValueError("cache title mismatch")
        return obj["article"]
    cache_dir.mkdir(parents=True,exist_ok=True)
    url=wiki.BASE+urllib.parse.quote(title,safe="")
    tmp=cache_dir/(key+".download")
    try:
        completed=subprocess.run(["curl.exe","-L","-sS","--fail-with-body",
            "--max-time",str(timeout),"-A",user_agent,
            "-H","Accept: application/json",
            "-w","%{http_code}","-o",str(tmp),url],
            check=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout+10)
        if completed.returncode or completed.stdout.strip()!="200":
            raise RuntimeError(f"curl request failed for {title}: exit={completed.returncode} "
                               f"HTTP={completed.stdout.strip()} stderr={completed.stderr[:300]}")
        doc=json.loads(tmp.read_text(encoding="utf-8-sig"))
        if not isinstance(doc,dict) or not isinstance(doc.get("source"),str) or \
           not isinstance(doc.get("id"),int) or doc.get("content_model")!="wikitext":
            raise ValueError("invalid REST Wikitext response")
        with path.open("x",encoding="utf-8") as f:
            json.dump({"requested_title":title,"article":doc},f,ensure_ascii=False)
        return doc
    finally:
        tmp.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--user-agent",required=True)
    p.add_argument("--titles",type=Path,default=Path("data/foundation_wikipedia_titles_v013586.txt"))
    p.add_argument("--output-dir",type=Path,default=Path("results/wikipedia_wikitext_v013589"))
    p.add_argument("--cache-dir",type=Path,default=Path("results/wikipedia_curl_cache_v013589"))
    p.add_argument("--delay",type=float,default=2.)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if not a.titles.is_file():p.error("missing article titles")
    if a.delay<1:p.error("delay must be at least 1 second")
    if "https://" not in a.user_agent and "@" not in a.user_agent:p.error("contact user agent required")
    titles=[x.strip() for x in a.titles.read_text(encoding="utf-8-sig").splitlines()
            if x.strip() and not x.startswith("#")]
    if not titles or len(set(titles))!=len(titles) or len(titles)>100:p.error("invalid titles")
    outputs=[a.output_dir/x for x in ("train.txt","train_records.jsonl","eval_records.jsonl","manifest.json")]
    if any(x.exists() for x in outputs):p.error("output exists; refusing overwrite")
    print(json.dumps({"version":"v0.13.58.9","preflight":"PASS","titles":len(titles),"run":a.run}))
    if not a.run:return
    def get(title):
        cachepath=a.cache_dir/(hashlib.sha256(title.encode("utf-8")).hexdigest()+".json")
        cached=cachepath.exists()
        doc=curl_article(title,a.user_agent,a.cache_dir)
        if not cached:time.sleep(a.delay)
        return doc
    train,ev,manifest=wiki.process(titles,get)
    if not train or not ev or {x["article_id"] for x in train}&{x["article_id"] for x in ev}:
        p.error("nonempty, disjoint article partitions required")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    with outputs[0].open("x",encoding="utf-8",newline="\n") as f:
        for item in train:f.write(item["text"]+"\n")
    for path,items in ((outputs[1],train),(outputs[2],ev)):
        with path.open("x",encoding="utf-8") as f:
            for item in items:f.write(json.dumps(item,ensure_ascii=False)+"\n")
    report={"version":"v0.13.58.9","status":"ACQUIRED_UNREVIEWED",
            "train_sentences":len(train),"eval_sentences":len(ev),
            "train_article_count":len({x["article_id"] for x in train}),
            "eval_article_count":len({x["article_id"] for x in ev}),
            "articles":manifest,"human_quality_reviewed":False,
            "training_approved":False,"license_reviewed":False,
            "historical_exposure_excluded":False}
    with outputs[3].open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ("status","train_sentences","eval_sentences",
          "train_article_count","eval_article_count")},ensure_ascii=False))
if __name__=="__main__":main()
