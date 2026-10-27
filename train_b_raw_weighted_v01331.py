"""v0.13.31 B_RAW weighted answer-start SFT ablation.

All runs start from same base with identical dataset, LR, replay and 8 epochs.
No production promotion. --run performs separate candidate training.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl

VARIANTS=(("STANDARD",0,1.0),("FIRST1_X4",1,4.0),("FIRST8_X4",8,4.0))

def plan(prefix):
    return [{"variant":name,"count":count,"weight":weight,
             "checkpoint":str(prefix)+f"_{name}.pt",
             "state":str(prefix)+f"_{name}_state.json"} for name,count,weight in VARIANTS]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--prefix",type=Path,default=Path("results/b_raw_weighted_v01331"))
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.epochs<1:p.error("epochs must be >= 1")
    if not a.data.exists():p.error(f"missing input {a.data}")
    rows=load_jsonl(a.data)
    if not rows or any(x.get("answer_format")!="B_RAW" or x.get("approval_state")!="UNAPPROVED" for x in rows):
        p.error("expected nonempty B_RAW unapproved training set")
    jobs=plan(a.prefix)
    report={"version":"v0.13.31","pairs":len(rows),"epochs":a.epochs,"lr":5e-6,
            "jobs":jobs,"status":"DRY_RUN","production_unchanged":True}
    if not a.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    for file in (a.base,a.tokenizer):
        if not file.exists():p.error(f"missing {file}")
    paths=[Path(j[k]) for j in jobs for k in ("checkpoint","state")]
    manifest=Path(str(a.prefix)+"_manifest.json")
    if any(pth.exists() for pth in paths+[manifest]):p.error("experiment artifacts exist; choose a new --prefix")
    manifest.parent.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for job in jobs:
        cmd=[sys.executable,"online_train.py","--chat-data",str(a.data),
            "--base-model",str(a.base),"--tokenizer",str(a.tokenizer),
            "--output",job["checkpoint"],"--state",job["state"],
            "--epochs",str(a.epochs),"--learning-rate","0.000005","--patience",str(a.epochs+1),
            "--early-token-count",str(job["count"]),"--early-token-weight",str(job["weight"])]
        code=subprocess.run(cmd,check=False).returncode
        outputs.append({**job,"returncode":code})
        if code:break
    report.update(status="COMPLETED" if len(outputs)==len(jobs) and all(x["returncode"]==0 for x in outputs) else "FAILED",
                  results=outputs)
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["status"]!="COMPLETED":raise SystemExit(1)

if __name__=="__main__":main()
