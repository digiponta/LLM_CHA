"""v0.13.29 independent B_RAW epoch sweep; no production promotion.

Runs 1/2/4/8 epochs from a common checkpoint. Each candidate writes to a
separate state file. Same QA dataset and training controls for every run.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl

EPOCHS=(1,2,4,8)
def plan(prefix,epochs=EPOCHS):
    return [{"epochs":int(e),"checkpoint":str(prefix)+f"_E{e}.pt",
             "state":str(prefix)+f"_E{e}_state.json"} for e in epochs]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--prefix",type=Path,default=Path("results/b_raw_epoch_v01329"))
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if not a.data.exists():p.error(f"missing data {a.data}")
    rows=load_jsonl(a.data)
    if not rows:p.error("empty B_RAW dataset")
    if any(r.get("answer_format")!="B_RAW" or r.get("approval_state")!="UNAPPROVED" for r in rows):
        p.error("expected B_RAW / UNAPPROVED dataset")
    jobs=plan(a.prefix)
    report={"version":"v0.13.29","pairs":len(rows),"epochs":list(EPOCHS),
            "status":"DRY_RUN","jobs":jobs,"production_unchanged":True}
    if not a.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    for path in (a.base,a.tokenizer):
        if not path.exists():p.error(f"missing {path}")
    a.prefix.parent.mkdir(parents=True,exist_ok=True)
    result=[]
    for job in jobs:
        ckpt=Path(job["checkpoint"]);state=Path(job["state"])
        if ckpt.exists() or state.exists():
            p.error(f"already exists: {ckpt} / {state}; choose another --prefix")
        cmd=[sys.executable,"online_train.py","--chat-data",str(a.data),
            "--base-model",str(a.base),"--tokenizer",str(a.tokenizer),
            "--output",str(ckpt),"--state",str(state),
            "--epochs",str(job["epochs"]),"--learning-rate","0.000005",
            "--patience","9"]
        rc=subprocess.run(cmd,check=False).returncode
        result.append({**job,"returncode":rc})
        if rc:break
    report.update(status="COMPLETED" if len(result)==len(jobs) and all(x["returncode"]==0 for x in result) else "FAILED",
                  results=result)
    out=Path(str(a.prefix)+"_manifest.json")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["status"]!="COMPLETED":raise SystemExit(1)
if __name__=="__main__":main()
