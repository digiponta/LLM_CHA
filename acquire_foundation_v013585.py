"""v0.13.58.5 foundation acquisition and provenance audit.

Explicit sources, source-level manifests, exact and character-ngram overlap
against reserved data. This is a candidate builder, not an approval process.
No network access or automatic invented text. --run writes candidate only.
"""
import argparse,hashlib,json,re
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):
    return [" ".join(x.split()) for x in p.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
def ngrams(s,n=5):
    s=re.sub(r"\s+","",s)
    return {s[i:i+n] for i in range(max(0,len(s)-n+1))}
def max_overlap(s,reference,ngram=5):
    a=ngrams(s,ngram)
    if not a:return 0.
    return max((len(a&b)/len(a|b) for b in reference if b),default=0.)
def collect(sources,reserved,min_chars=12,similarity_threshold=.8):
    if not sources:raise ValueError("explicit source files required")
    if not 0<=similarity_threshold<=1:raise ValueError("bad similarity threshold")
    seen_files=set();reference=[];reserved_set=set()
    for p in reserved:
        if not p.is_file():raise FileNotFoundError(p)
        for s in lines(p):
            reserved_set.add(s);reference.append(ngrams(s))
    output=[];seen=set();audit=[]
    for p in sources:
        if not p.is_file():raise FileNotFoundError(p)
        if p.suffix.lower()!=".txt":raise ValueError("plain text .txt required")
        if any(term in p.name.lower() for term in ("holdout","_val","test","review","unapproved","candidate")):
            raise ValueError("potential evaluation/unapproved source")
        if p.resolve() in seen_files:raise ValueError("repeated source path")
        seen_files.add(p.resolve())
        stats={"source":str(p),"sha256":sha(p),"total":0,"accepted":0,
               "short":0,"exact_duplicate":0,"reserved_exact":0,
               "near_reserved":0}
        for s in lines(p):
            stats["total"]+=1
            if len(s)<min_chars:stats["short"]+=1;continue
            if s in reserved_set:stats["reserved_exact"]+=1;continue
            if s in seen:stats["exact_duplicate"]+=1;continue
            if max_overlap(s,reference)>=similarity_threshold:
                stats["near_reserved"]+=1;continue
            output.append(s);seen.add(s);stats["accepted"]+=1
        audit.append(stats)
    return output,{"version":"v0.13.58.5","status":"CANDIDATE_ONLY",
        "candidate_sentences":len(output),"source_audit":audit,
        "reserved_files":[str(p) for p in reserved],
        "near_duplicate_metric":"character 5-gram Jaccard against reserved lines",
        "near_duplicate_threshold":similarity_threshold,
        "human_quality_reviewed":False,"source_independence_verified":False,
        "training_approved":False,
        "limitations":["Near-duplicate check is lexical only, not semantic.",
                       "Historical checkpoint data exposure not excluded.",
                       "Review provenance, licensing and quality before learning."]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,action="append",required=True)
    p.add_argument("--reserved",type=Path,action="append",default=[])
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--min-chars",type=int,default=12)
    p.add_argument("--near-threshold",type=float,default=.8)
    p.add_argument("--min-sentences",type=int,default=1000)
    p.add_argument("--output",type=Path,default=Path("results/foundation_acquired_v013585.txt"))
    p.add_argument("--report",type=Path,default=Path("results/foundation_acquisition_audit_v013585.json"))
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.min_chars<1 or a.min_sentences<1:p.error("minimums must be positive")
    for f in [*a.source,*a.reserved,a.tokenizer]:
        if not f.is_file():p.error(f"missing: {f}")
    if a.output.exists() or a.report.exists():p.error("refusing overwrite")
    if len({p.resolve() for p in [*a.source,*a.reserved,a.tokenizer,a.output,a.report]})!=len(a.source)+len(a.reserved)+3:
        p.error("duplicate or colliding paths")
    rows,report=collect(a.source,a.reserved,a.min_chars,a.near_threshold)
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(a.tokenizer))
    report["bpe_tokens"]=sum(len(tok.encode(s,add_bos=True,add_eos=True)) for s in rows)
    report["min_sentences"]=a.min_sentences
    report["scale_ready"]=len(rows)>=a.min_sentences
    report["tokenizer_sha256"]=sha(a.tokenizer)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not a.run:return
    if not report["scale_ready"]:p.error("insufficient scale; no outputs written")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf-8",newline="\n") as f:f.write("\n".join(rows)+"\n")
    with a.report.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("candidate:",a.output,"audit:",a.report)
if __name__=="__main__":main()
