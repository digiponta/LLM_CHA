"""v0.13.36 RPC scale sweep: 10k/30k/100k, fixed validation, same base.

Each candidate starts independently from the same base model. Train subsets are
nested and spread over conversations, not merely the first JSONL records.
Existing test data is reserved and never used for tuning.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SIZES=(10000,30000,100000)

def stable_score(value):
    return hashlib.sha256(("rpc-scale-v01336:"+str(value)).encode()).hexdigest()

def dispersed_nested(rows):
    """Stable per-dialogue round-robin sampling, with deterministic dialogue order."""
    groups={}
    for r in rows:
        groups.setdefault(str(r["dialogue_id"]),[]).append(r)
    keys=sorted(groups,key=stable_score)
    order=[]
    longest=max(map(len,groups.values()))
    for j in range(longest):
        for key in keys:
            if j<len(groups[key]):
                order.append(groups[key][j])
    return order

def check_split(train,val,test):
    ids=[{str(r["dialogue_id"]) for r in x} for x in (train,val,test)]
    if ids[0]&ids[1] or ids[0]&ids[2] or ids[1]&ids[2]:
        raise ValueError("dialogue-level train/val/test overlap")

def load(path):
    with path.open(encoding="utf-8") as f:
        rows=[json.loads(l) for l in f if l.strip()]
    if any(r.get("source")!="rpc-dialogue-sft" or r.get("approval_state")!="UNAPPROVED"
           or "dialogue_id" not in r or not r.get("user") or not r.get("assistant") for r in rows):
        raise ValueError(f"invalid RPC SFT data: {path}")
    return rows

def write_jsonl(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    with path.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")

def make_plans(args,train):
    return [{"size":size,
             "data_dir":str(args.output_dir/f"data_{size}"),
             "checkpoint":str(args.output_dir/f"rpc_candidate_{size}.pt"),
             "report":str(args.output_dir/f"rpc_train_{size}.json")}
            for size in SIZES if size<=len(train)]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",type=Path,default=Path("results/rpc_sft_full_v01333"))
    p.add_argument("--output-dir",type=Path,default=Path("results/rpc_sweep_v01336"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--val-limit",type=int,default=1000)
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--lr",type=float,default=0.000005)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if min(a.val_limit,a.epochs,a.batch_size)<1 or a.lr<=0:p.error("invalid hyperparameters")
    files={k:a.data_dir/f"rpc_sft_{k}_v01333.jsonl" for k in ("train","val","test")}
    for f in files.values():
        if not f.exists():p.error(f"missing {f}")
    raw={k:load(f) for k,f in files.items()}
    check_split(raw["train"],raw["val"],raw["test"])
    train=dispersed_nested(raw["train"])
    val=raw["val"][:a.val_limit]
    if len(val)<a.val_limit:p.error("not enough validation examples")
    plans=make_plans(a,train)
    if len(plans)!=len(SIZES):p.error("not enough training pairs")
    summary={"version":"v0.13.36","status":"DRY_RUN","train_total":len(train),
             "validation_fixed":len(val),"test_reserved":len(raw["test"]),
             "sizes":[x["size"] for x in plans],
             "sampling":"stable dialogue round robin nested",
             "all_same_base":str(a.base),"epochs":a.epochs,"batch_size":a.batch_size,"lr":a.lr,
             "production_unchanged":True,"runs":[]}
    if not a.run:
        print(json.dumps(summary,ensure_ascii=False,indent=2));return
    if not a.base.exists() or not a.tokenizer.exists():p.error("missing base/tokenizer")
    for job in plans:
        d=Path(job["data_dir"])
        for k in ("train","val","test"):
            if (d/f"rpc_sft_{k}_v01333.jsonl").exists():
                p.error(f"output exists: {d}")
        if Path(job["checkpoint"]).exists() or Path(job["report"]).exists():
            p.error(f"candidate/report exists for size {job['size']}")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    manifest=a.output_dir/"sweep_manifest_v01336.json"
    if manifest.exists():p.error("manifest exists")
    # Each run passes its own fixed validation subset. Test is a minimal
    # non-tuning sentinel only: the trainer does not read its answer tokens.
    sentinel=raw["test"][:1]
    for job in plans:
        size=job["size"];d=Path(job["data_dir"])
        write_jsonl(d/"rpc_sft_train_v01333.jsonl",train[:size])
        write_jsonl(d/"rpc_sft_val_v01333.jsonl",val)
        write_jsonl(d/"rpc_sft_test_v01333.jsonl",sentinel)
        cmd=[sys.executable,"-X","utf8","train_rpc_dialogue_sft_v01334.py",
             "--data-dir",str(d),"--base",str(a.base),"--tokenizer",str(a.tokenizer),
             "--output",job["checkpoint"],"--report",job["report"],
             "--train-limit",str(size),"--val-limit",str(len(val)),
             "--test-limit","1","--epochs",str(a.epochs),
             "--batch-size",str(a.batch_size),"--lr",str(a.lr),"--run"]
        rc=subprocess.run(cmd,check=False).returncode
        entry={"size":size,"returncode":rc,"report":job["report"],"checkpoint":job["checkpoint"]}
        if rc==0:
            measured=json.loads(Path(job["report"]).read_text(encoding="utf-8"))
            entry.update({"base_val_nll":measured["base_val_nll"],
                          "best_val_nll":measured["best_val_nll"],
                          "best_epoch":measured["best_epoch"]})
        summary["runs"].append(entry)
        if rc:break
        manifest.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary["status"]="COMPLETED" if len(summary["runs"])==len(plans) and all(x["returncode"]==0 for x in summary["runs"]) else "FAILED"
    manifest.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if summary["status"]!="COMPLETED":raise SystemExit(1)
if __name__=="__main__":main()
