"""v0.13.58.19: read-only Wiki cleaner v2 for previously extracted JSONL.

Re-processes unapproved candidate article text. Invalid paragraphs are
quarantined; there is NO training, approval or semantic promotion. Since the
v0.13.58.18 extractor already discarded some source markup, this pass cannot
restore missing content: for best results re-extract raw dump with a proper
wikitext parser in a future separate experiment.
"""
import argparse,hashlib,html,json,re
from pathlib import Path

BAD = [
    re.compile(r"\]\]|\[\[|\{\{|\}\}|\{\||\|\}"),
    re.compile(r"<(?:ref|gallery|math|table)\b",re.I),
    re.compile(r"\b(?:File|Image|ファイル|画像):",re.I),
]
def clean_paragraph(text):
    s=html.unescape(text)
    s=re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]",r"\1",s)
    s=re.sub(r"(?m)^\s*[|!].*$","",s)
    s=re.sub(r"(?m)^\s*[\{\|].*$","",s)
    s=re.sub(r"(?m)^\s*(?:\[\[?(?:ファイル|画像|File|Image):).*$","",s,flags=re.I)
    s=re.sub(r"\s+"," ",s).strip()
    return s

def assess(text,min_chars=100):
    errors=[]
    if len(text)<min_chars:errors.append("TOO_SHORT")
    for i,r in enumerate(BAD):
        if r.search(text):errors.append(("MARKUP","TAG_FRAGMENT","MEDIA_FRAGMENT")[i])
    if any(ord(x)==0xfffd for x in text):errors.append("REPLACEMENT_CHAR")
    if re.search(r"(?:\s|^)[\|\]](?:\s|$)",text):errors.append("ORPHAN_DELIMITER")
    if text.count("「")!=text.count("」"):errors.append("UNBALANCED_QUOTE")
    if text.count("（")!=text.count("）"):errors.append("UNBALANCED_PAREN")
    return errors

def build(source,outdir,min_chars=100):
    if outdir.exists():raise FileExistsError(outdir)
    accepted=[];quarantine=[];article_count=0;source_lines=0
    with source.open("r",encoding="utf-8-sig") as stream:
        for line_number,line in enumerate(stream,1):
            if not line.strip():continue
            obj=json.loads(line);article_count+=1
            if obj.get("approval")!="PENDING_REVIEW" or obj.get("auto_promote") is not False:
                raise ValueError(f"unsafe candidate at {line_number}")
            if not isinstance(obj.get("text"),str) or not isinstance(obj.get("page_id"),str):
                raise ValueError(f"invalid candidate at {line_number}")
            for j,p in enumerate(re.split(r"\n\s*\n",obj["text"])):
                if not p.strip():continue
                source_lines+=1
                content=clean_paragraph(p)
                reasons=assess(content,min_chars)
                record={"article_id":obj["page_id"],"title":obj["title"],
                    "source_url":obj["url"],"paragraph_index":j,"text":content,
                    "approval":"PENDING_REVIEW","auto_promote":False}
                if reasons:quarantine.append({**record,"reasons":reasons})
                else:accepted.append(record)
    if not accepted and not quarantine:raise ValueError("empty candidate source")
    outdir.mkdir(parents=True,exist_ok=False)
    with (outdir/"clean_corpus.txt").open("x",encoding="utf-8") as f:
        for r in accepted:f.write(r["text"]+"\n")
    for filename,rows in (("clean_candidates.jsonl",accepted),("quarantine.jsonl",quarantine)):
        with (outdir/filename).open("x",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    report={"version":"v0.13.58.19","status":"QUALITY_REVIEW_REQUIRED",
        "source":str(source),"articles":article_count,"paragraphs_input":source_lines,
        "accepted":len(accepted),"quarantined":len(quarantine),
        "acceptance_ratio":len(accepted)/max(source_lines,1),
        "reason_counts":{reason:sum(reason in x["reasons"] for x in quarantine)
                         for reason in sorted(set(y for x in quarantine for y in x["reasons"]))},
        "sha256":{name:hashlib.sha256((outdir/name).read_bytes()).hexdigest()
                  for name in ("clean_corpus.txt","clean_candidates.jsonl","quarantine.jsonl")},
        "limitations":["Heuristic filtering may reject valid paragraphs",
         "Markup removed by v0.13.58.18 cannot be reconstructed",
         "Cleaned text is not independently verified or approved",
         "Article-level source attribution must be preserved on redistribution"],
        "training_performed":False,"memory_promoted":False,"production_promotion_allowed":False}
    (outdir/"quality_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("results/jawiki_extract_v0135818/jawiki_semantic_candidates.jsonl"))
    p.add_argument("--output-dir",type=Path,default=Path("results/jawiki_clean_v0135819"))
    p.add_argument("--min-chars",type=int,default=100)
    a=p.parse_args()
    if not a.source.is_file():p.error("source missing: "+str(a.source))
    if a.min_chars<1:p.error("min-chars must be positive")
    report=build(a.source,a.output_dir,a.min_chars)
    print(json.dumps({k:report[k] for k in ("status","articles","paragraphs_input","accepted","quarantined","acceptance_ratio")},ensure_ascii=False))
    print("report:",a.output_dir/"quality_report.json")
if __name__=="__main__":main()
