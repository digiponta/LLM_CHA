"""v0.13.58.4: build an audited, training-only Japanese foundation candidate.

Never silently treat literature, validation, holdout, unapproved knowledge, or
generated model outputs as independent foundation data. Explicit --source
arguments select candidate UTF-8 text documents. Default is audit-only.
"""
import argparse,hashlib,json,re
from pathlib import Path

BLOCKED=("holdout","_val","validation","_test","review","unapproved","candidate","generated")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(s):return " ".join(s.strip().split())
def read_lines(p):
    return [normalize(x) for x in p.read_text(encoding="utf-8-sig").splitlines() if normalize(x)]
def build(sources,reserved,minimum=30):
    if not sources:raise ValueError("explicit --source required")
    if minimum<1:raise ValueError("minimum must be positive")
    seen_paths=set()
    for path in sources:
        if any(x in path.name.lower() for x in BLOCKED):
            raise ValueError(f"refusing possible eval/unapproved source: {path}")
        if path.suffix.lower()!=".txt":raise ValueError("only plain UTF-8 .txt inputs")
        if not path.is_file():raise FileNotFoundError(path)
        if path.resolve() in seen_paths:raise ValueError("duplicate source file")
        seen_paths.add(path.resolve())
    reserved_text=set()
    for path in reserved:
        if not path.is_file():raise FileNotFoundError(path)
        if path.suffix.lower()!=".txt":raise ValueError("reserved files must be .txt")
        reserved_text.update(read_lines(path))
    rows=[];seen=set();stats={}
    for path in sources:
        s={"total_lines":0,"included":0,"duplicates":0,"reserved_overlap":0}
        for line in read_lines(path):
            s["total_lines"]+=1
            if line in reserved_text:
                s["reserved_overlap"]+=1;continue
            if line in seen:
                s["duplicates"]+=1;continue
            seen.add(line);rows.append(line);s["included"]+=1
        stats[str(path)]=s
    return rows,{"version":"v0.13.58.4",
                 "status":"CANDIDATE_READY" if len(rows)>=minimum else "INSUFFICIENT_FOUNDATION",
                 "candidate_sentences":len(rows),"minimum_sentences":minimum,
                 "sources":stats,"reserved_source_count":len(reserved),
                 "independent_holdout_verified":False,"human_quality_reviewed":False,
                 "training_approved":False,
                 "limitations":["Literal line exclusion is not semantic leakage detection.",
                    "Text may have been previously exposed to model training.",
                    "Do not mistake same-novel literature for independent foundation."]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,action="append",required=True)
    p.add_argument("--reserved",type=Path,action="append",default=[])
    p.add_argument("--minimum",type=int,default=30)
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/foundation_candidate_v013584.txt"))
    p.add_argument("--report",type=Path,default=Path("results/foundation_audit_v013584.json"))
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if not a.tokenizer.is_file():p.error("tokenizer missing")
    if a.output.resolve() in {x.resolve() for x in [*a.source,*a.reserved,a.tokenizer,a.report]}:
        p.error("output overlaps input")
    if a.report.resolve() in {x.resolve() for x in [*a.source,*a.reserved,a.tokenizer]}:
        p.error("report overlaps input")
    if a.output.exists() or a.report.exists():p.error("output exists; refusing overwrite")
    rows,report=build(a.source,a.reserved,a.minimum)
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(a.tokenizer))
    report["bpe_tokens"]=sum(len(tok.encode(x,add_bos=True,add_eos=True)) for x in rows)
    report["input_sha256"]={str(x):sha(x) for x in [*a.source,*a.reserved,a.tokenizer]}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not a.run:return
    if report["status"]!="CANDIDATE_READY":p.error("insufficient data; no output written")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf-8",newline="\n") as f:f.write("\n".join(rows)+"\n")
    with a.report.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("written:",a.output,a.report)
if __name__=="__main__":main()
