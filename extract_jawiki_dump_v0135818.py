"""v0.13.58.18: bounded, offline Japanese Wikipedia XML dump extractor.

Produce *unapproved candidates*; no ingestion, memory promotion, or training.
Parse XML incrementally; article text is cleaned conservatively.
"""
import argparse,bz2,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_SOURCE=Path(r"C:\Users\inoma\git\misc\LLM\data\jawiki-latest-pages-articles.xml.bz2")
def local_name(tag):return tag.rsplit("}",1)[-1]
def child_text(elem,name):
    for child in elem:
        if local_name(child.tag)==name:return child.text or ""
    return ""
def extract_page(page):
    title=child_text(page,"title")
    ns=child_text(page,"ns")
    revision=next((x for x in page if local_name(x.tag)=="revision"),None)
    if revision is None:return None
    raw=child_text(revision,"text")
    page_id=child_text(page,"id")
    if ns!="0" or not title or not raw or title.startswith(("一覧","Template:")):
        return None
    if raw.lstrip().upper().startswith("#REDIRECT") or raw.lstrip().startswith("#転送"):
        return None
    return {"page_id":page_id,"title":title,"raw":raw}
def clean_wikitext(text):
    # Remove deeply nested templates without relying on fragile regex nesting.
    out=[];level=0;i=0
    while i<len(text):
        if text.startswith("{{",i):
            level+=1;i+=2;continue
        if level and text.startswith("}}",i):
            level-=1;i+=2;continue
        if level:
            i+=1;continue
        if text.startswith("<!--",i):
            end=text.find("-->",i+4)
            i=len(text) if end<0 else end+3;continue
        out.append(text[i]);i+=1
    t="".join(out)
    t=re.sub(r"<ref\b[^>]*>.*?</ref\s*>","",t,flags=re.S|re.I)
    t=re.sub(r"<ref\b[^>]*/>","",t,flags=re.I)
    t=re.sub(r"<[^>]+>"," ",t)
    t=re.sub(r"\[\[(?:File|Image|ファイル|画像|Category|カテゴリ):[^\]]+\]\]","",t,flags=re.I)
    t=re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]",r"\2",t)
    t=re.sub(r"\[\[([^\]]+)\]\]",r"\1",t)
    t=re.sub(r"\[(?:https?://)[^\s\]]+(?:\s+([^\]]+))?\]",lambda m:m.group(1) or "",t)
    t=re.sub(r"(?m)^\s*(?:\{\||\|\}|[|!].*|[;:].*|\*.*)$","",t)
    t=re.sub(r"(?m)^={2,}\s*(.*?)\s*={2,}\s*$",r"\1",t)
    t=re.sub(r"(?m)^#+\s*","",t)
    t=re.sub(r"'{2,5}","",t)
    t=re.sub(r"&nbsp;"," ",t)
    t=re.sub(r"[ \t]+"," ",t)
    t=re.sub(r"\n{3,}","\n\n",t)
    return t.strip()
def paragraphs(text,min_chars):
    return [p.strip() for p in re.split(r"\n\s*\n",text) if len(p.strip())>=min_chars]
def stream_articles(path,max_articles=100,min_chars=120):
    if max_articles<1 or min_chars<1:raise ValueError("invalid limits")
    with bz2.open(path,"rb") if path.suffix==".bz2" else path.open("rb") as fh:
        # Prefer end event processing; clear root after each page to bound memory.
        ctx=ET.iterparse(fh,events=("start","end"))
        _,root=next(ctx)
        count=0
        for event,node in ctx:
            if event!="end" or local_name(node.tag)!="page":continue
            page=extract_page(node)
            if page:
                body=clean_wikitext(page["raw"])
                ps=paragraphs(body,min_chars)
                if ps:
                    yield {"page_id":page["page_id"],"title":page["title"],
                           "source":"ja.wikipedia.org","paragraphs":ps}
                    count+=1
            root.clear()
            if count>=max_articles:break

def run(source,outdir,max_articles,min_chars):
    if not source.is_file():raise FileNotFoundError(source)
    if outdir.exists():raise FileExistsError("output directory already exists: "+str(outdir))
    # Input source may be very large: hash only emitted article content,
    # not the entire compressed dump.
    records=list(stream_articles(source,max_articles,min_chars))
    if not records:raise RuntimeError("No clean articles passed filters")
    outdir.mkdir(parents=True,exist_ok=False)
    corpus=outdir/"jawiki_corpus.txt";candidates=outdir/"jawiki_semantic_candidates.jsonl"
    manifest=outdir/"manifest.json"
    with corpus.open("x",encoding="utf-8") as f, candidates.open("x",encoding="utf-8") as g:
        for item in records:
            for p in item["paragraphs"]:
                f.write(p.replace("\n"," ")+"\n")
            candidate={"title":item["title"],"page_id":item["page_id"],
                "source":"ja.wikipedia.org","url":"https://ja.wikipedia.org/?curid="+item["page_id"],
                "text":"\n\n".join(item["paragraphs"]),
                "approval":"PENDING_REVIEW","truth_state":"EXTERNAL_UNVERIFIED",
                "auto_promote":False,"training_approved":False}
            g.write(json.dumps(candidate,ensure_ascii=False)+"\n")
    data={"version":"v0.13.58.18","status":"UNAPPROVED_EXTRACTION",
       "input_path":str(source),"articles":len(records),
       "paragraphs":sum(len(x["paragraphs"]) for x in records),
       "max_articles":max_articles,"minimum_paragraph_chars":min_chars,
       "files":{"corpus":str(corpus),"candidates":str(candidates)},
       "sha256":{"corpus":hashlib.sha256(corpus.read_bytes()).hexdigest(),
                 "candidates":hashlib.sha256(candidates.read_bytes()).hexdigest()},
       "limitations":["Conservative wikitext cleanup is not a complete MediaWiki parser",
                      "Markup or citation fragments may remain; human review required",
                      "Wikipedia content may be inaccurate, biased, or copyrighted under attribution/share-alike terms",
                      "Not an independent evaluation set"],
       "training_performed":False,"memory_promoted":False,
       "production_promotion_allowed":False}
    manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=DEFAULT_SOURCE)
    p.add_argument("--output-dir",type=Path,default=Path("results/jawiki_extract_v0135818"))
    p.add_argument("--max-articles",type=int,default=100)
    p.add_argument("--min-chars",type=int,default=120)
    args=p.parse_args()
    r=run(args.source,args.output_dir,args.max_articles,args.min_chars)
    print(json.dumps({"status":r["status"],"articles":r["articles"],"paragraphs":r["paragraphs"],"training_performed":False},ensure_ascii=False))
    print("manifest:",args.output_dir/"manifest.json")
if __name__=="__main__":main()
