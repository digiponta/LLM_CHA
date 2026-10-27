"""v0.13.43: audit Japanese foundation corpus, group split by source, no training.

Manifest JSON:
{"sources":[{"id":"unique-id","path":"data/foo.txt","license":"...","provenance":"...",
             "approved_for_training":true}, ...]}
One source/work is assigned wholly to train or validation. External holdout files
MUST NOT appear in manifest. Source-independent split, not proof of independence
from historical checkpoints.
"""
import argparse,hashlib,json,random,re
from pathlib import Path

def clean_lines(path,min_chars=20,max_chars=500):
    raw=Path(path).read_text(encoding="utf-8-sig")
    seen=set(); rows=[]
    for line in raw.splitlines():
        s=re.sub(r"\s+"," ",line).strip()
        if len(s)<min_chars or len(s)>max_chars:continue
        if "�" in s or "\x00" in s:continue
        if not re.search(r"[。！？!?]$",s):continue
        if s in seen:continue
        seen.add(s);rows.append(s)
    return rows

def partition_sources(sources,val_ratio=0.2,seed=1343):
    if not (0<val_ratio<1):raise ValueError("val_ratio must be between 0 and 1")
    if len(sources)<2:raise ValueError("need at least two independent sources")
    shuffled=sorted(sources,key=lambda s:s["id"])
    random.Random(seed).shuffle(shuffled)
    count=max(1,min(len(shuffled)-1,round(len(shuffled)*val_ratio)))
    valids={row["id"] for row in shuffled[:count]}
    return {row["id"]:("val" if row["id"] in valids else "train") for row in shuffled}

def prepare(manifest,base,val_ratio=.2,seed=1343,forbidden=None):
    sources=manifest["sources"]
    ids=[s["id"] for s in sources]
    if len(set(ids))!=len(ids):raise ValueError("duplicate source id")
    if len(sources)<2:raise ValueError("need at least two sources")
    forbidden={Path(p).resolve() for p in (forbidden or [])}
    paths=set(); audit=[]; clean={}
    for entry in sources:
        if not all(entry.get(k) for k in ("id","path","license","provenance")):
            raise ValueError("missing source id/path/license/provenance")
        if entry.get("approved_for_training") is not True:
            raise ValueError(f"source not approved for training: {entry['id']}")
        path=(base/entry["path"]).resolve()
        if path in forbidden or "heldout" in path.name.lower():
            raise ValueError(f"holdout source forbidden: {path}")
        if not path.is_file():raise FileNotFoundError(path)
        if path in paths:raise ValueError("duplicate source path")
        paths.add(path)
        rows=clean_lines(path)
        if not rows:raise ValueError(f"no valid lines in {path}")
        clean[entry["id"]]=rows
        audit.append({"id":entry["id"],"path":str(path),"license":entry["license"],
                      "provenance":entry["provenance"],"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "eligible_sentences":len(rows)})
    split=partition_sources(sources,val_ratio,seed)
    result={"train":[],"val":[]}; owners={}
    duplicates=[]
    for entry in sources:
        for sentence in clean[entry["id"]]:
            if sentence in owners:
                duplicates.append({"first":owners[sentence],"second":entry["id"]})
                continue
            owners[sentence]=entry["id"]
            result[split[entry["id"]]].append(sentence)
    if not result["train"] or not result["val"]:
        raise ValueError("one split has no sentences")
    return result,{"version":"v0.13.43","split":"SOURCE_GROUPED","seed":seed,
                   "source_audit":audit,"assignments":split,
                   "counts":{k:len(v) for k,v in result.items()},
                   "cross_source_duplicates_dropped":duplicates,
                   "holdout_independence_verified":False,
                   "notes":["Document-level grouping prevents within-manifest source crossover.",
                            "Approval flag is supplied by operator, not verified by this program.",
                            "Historical checkpoint exposure must be separately audited."]}

def write_new(path,data):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(data,encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,default=Path("results/japanese_foundation_corpus_v01343"))
    ap.add_argument("--seed",type=int,default=1343)
    ap.add_argument("--val-ratio",type=float,default=.2)
    ap.add_argument("--exclude",type=Path,action="append",default=[])
    a=ap.parse_args()
    manifest=json.loads(a.manifest.read_text(encoding="utf-8-sig"))
    prepared,audit=prepare(manifest,a.manifest.parent,a.val_ratio,a.seed,a.exclude)
    output=a.output_dir
    targets=[output/"train.txt",output/"val.txt",output/"audit.json"]
    if any(p.exists() for p in targets):ap.error("output exists; refusing overwrite")
    for name in ("train","val"):
        write_new(output/f"{name}.txt","\n".join(prepared[name])+"\n")
    write_new(output/"audit.json",json.dumps(audit,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(audit["counts"],ensure_ascii=False))
    print("audit:",output/"audit.json")
if __name__=="__main__":main()
