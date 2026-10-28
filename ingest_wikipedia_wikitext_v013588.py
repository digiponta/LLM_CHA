"""v0.13.58.8: ingest Japanese Wikipedia REST page source (Wikitext).

Explicit titles, bounded requests, page-level split, provenance and no
automatic training approval. Requires: pip install mwparserfromhell
"""
import argparse,hashlib,json,re,time,urllib.parse,urllib.request
from pathlib import Path

BASE="https://ja.wikipedia.org/w/rest.php/v1/page/"
def partition(pageid,eval_percent=20):
    if not 1<=eval_percent<=50:raise ValueError("bad eval percent")
    v=int(hashlib.sha256(f"foundation-v013588:{pageid}".encode()).hexdigest()[:12],16)%100
    return "eval" if v<eval_percent else "train"
def extract(source,min_chars=18):
    import mwparserfromhell
    code=mwparserfromhell.parse(source)
    # Remove sections likely to consist of citations and navigation, as well
    # as templates/tables/refs whose expansion requires MediaWiki runtime.
    parts=re.split(r"(?m)^={2,}\s*(?:脚注|注釈|出典|参考文献|関連項目|外部リンク|文献)\s*={2,}\s*$",source,maxsplit=1)
    code=mwparserfromhell.parse(parts[0])
    for tag in list(code.filter_tags(recursive=True)):
        if str(tag.tag).strip().lower() in ("ref","gallery","math","nowiki","timeline"):
            try:code.remove(tag)
            except ValueError:pass
    for template in list(code.filter_templates(recursive=True)):
        try:code.remove(template)
        except ValueError:pass
    text=code.strip_code(normalize=True,collapse=True)
    text=re.sub(r"\s+"," ",text)
    text=re.sub(r"\[[0-9０-９]+\]","",text)
    # Conservative: skip sentences still containing markup artifacts.
    return [s.strip() for s in re.split(r"(?<=[。！？])\s*",text)
            if min_chars<=len(s.strip())<=350 and re.search(r"[。！？]$",s.strip())
            and not re.search(r"[{}\[\]|<>]",s)]
def fetch(title,user_agent,timeout=30):
    url=BASE+urllib.parse.quote(title,safe="")
    req=urllib.request.Request(url,headers={"User-Agent":user_agent,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=json.load(r)
    if not isinstance(data,dict) or not isinstance(data.get("source"),str):
        raise ValueError(f"missing Wikitext source for {title}")
    if not isinstance(data.get("id"),int):raise ValueError("missing article ID")
    if data.get("content_model")!="wikitext":raise ValueError("unsupported content model")
    return data
def process(titles,get,min_chars=18,eval_percent=20):
    train=[];evaluation=[];manifest=[];ids=set()
    for title in titles:
        doc=get(title);pid=doc["id"]
        if pid in ids:continue
        ids.add(pid)
        category=partition(pid,eval_percent)
        rows=list(dict.fromkeys(extract(doc["source"],min_chars)))
        url="https://ja.wikipedia.org/wiki/"+urllib.parse.quote(doc.get("title",title).replace(" ","_"),safe="")
        info={"id":pid,"title":doc.get("title",title),"revision":doc.get("latest",{}),
              "license":doc.get("license"),"url":url,"split":category,
              "sentences":len(rows),"wikitext_sha256":hashlib.sha256(doc["source"].encode("utf-8")).hexdigest()}
        manifest.append(info)
        for n,s in enumerate(rows):
            item={"article_id":pid,"title":info["title"],"source_url":url,
                  "revision":info["revision"],"sentence_index":n,"text":s}
            (train if category=="train" else evaluation).append(item)
    return train,evaluation,manifest
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--titles",type=Path,default=Path("data/foundation_wikipedia_titles_v013586.txt"))
    ap.add_argument("--user-agent",required=True)
    ap.add_argument("--output-dir",type=Path,default=Path("results/wikipedia_wikitext_v013588"))
    ap.add_argument("--delay",type=float,default=2.)
    ap.add_argument("--eval-percent",type=int,default=20)
    ap.add_argument("--run",action="store_true")
    a=ap.parse_args()
    if not a.titles.is_file():ap.error("missing titles")
    if not ("https://" in a.user_agent or "@" in a.user_agent):ap.error("user-agent must contain contact")
    if a.delay<1.:ap.error("delay must be at least 1 second")
    titles=[x.strip() for x in a.titles.read_text(encoding="utf-8-sig").splitlines()
            if x.strip() and not x.startswith("#")]
    if not titles or len(titles)>100 or len(titles)!=len(set(titles)):ap.error("invalid titles")
    output=[a.output_dir/x for x in ("train.txt","train_records.jsonl","eval_records.jsonl","manifest.json")]
    if any(p.exists() for p in output):ap.error("outputs already exist")
    print(json.dumps({"version":"v0.13.58.8","preflight":"PASS","titles":len(titles),"run":a.run}))
    if not a.run:return
    def paced(title):
        item=fetch(title,a.user_agent)
        time.sleep(a.delay)
        return item
    train,ev,manifest=process(titles,paced,eval_percent=a.eval_percent)
    if not train or not ev or {x["article_id"] for x in train}&{x["article_id"] for x in ev}:
        ap.error("non-empty disjoint article splits required")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    with output[0].open("x",encoding="utf-8",newline="\n") as f:
        for row in train:f.write(row["text"]+"\n")
    for path,rows in [(output[1],train),(output[2],ev)]:
        with path.open("x",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    report={"version":"v0.13.58.8","status":"ACQUIRED_UNREVIEWED",
            "train_sentences":len(train),"eval_sentences":len(ev),"articles":manifest,
            "train_article_count":len({x["article_id"] for x in train}),
            "eval_article_count":len({x["article_id"] for x in ev}),
            "human_quality_reviewed":False,"license_reviewed":False,
            "historical_exposure_excluded":False,"training_approved":False}
    with output[3].open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:report[k] for k in ("status","train_sentences","eval_sentences",
                     "train_article_count","eval_article_count")},ensure_ascii=False))
if __name__=="__main__":main()
