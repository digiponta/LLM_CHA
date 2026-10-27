"""v0.13.16: stage and optionally train combined Level-1/2 unapproved QA.

Default is a read-only dry run. Existing approval ledger is authoritative.
The pilot writes an isolated checkpoint, not the production model.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl
from online_train import pair_fingerprint, checkpoint_trained_fingerprints

L1=Path("results/unapproved_semantic_qa_v01314.jsonl")
L2=Path("results/unapproved_mention_qa_v01315.jsonl")
LEDGER=Path("data/unapproved_corpus_ledger_v0139.jsonl")
OUT=Path("results/combined_unapproved_qa_pilot_v01316.jsonl")
BASE=Path("model/model-gpu-v1.6.2-online.pt")
CANDIDATE=Path("model/model-gpu-v1.6.2-unapproved-qa-v01316.pt")
STATE=Path("results/unapproved_qa_state_v01316.json")

def combine(level1,level2,ledger,limit):
    approvals={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    # Interleave levels, rather than taking only the first source's examples.
    sources=[load_jsonl(level1),load_jsonl(level2)]
    selected=[]
    seen=set()
    positions=[0,0]
    while len(selected)<limit and any(positions[i]<len(sources[i]) for i in range(2)):
        for i in range(2):
            if len(selected)>=limit:break
            if positions[i]>=len(sources[i]):continue
            row=sources[i][positions[i]]
            positions[i]+=1
            kid=row.get("knowledge_id")
            approval=approvals.get(kid,row.get("approval_state","UNAPPROVED"))
            if approval=="REJECTED":continue
            question=row.get("user","").strip()
            answer=row.get("assistant","").strip()
            if not kid or not question or not answer:continue
            key=pair_fingerprint(question,answer)
            if key in seen:continue
            seen.add(key)
            selected.append({**row,"approval_state":approval,"truth_state":"UNVERIFIED",
                             "source":"corpus-unapproved","pair_fingerprint":key})
    return selected

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--level1",type=Path,default=L1)
    p.add_argument("--level2",type=Path,default=L2)
    p.add_argument("--ledger",type=Path,default=LEDGER)
    p.add_argument("--data",type=Path,default=OUT)
    p.add_argument("--base",type=Path,default=BASE)
    p.add_argument("--candidate",type=Path,default=CANDIDATE)
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--state",type=Path,default=STATE)
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--epochs",type=int,default=1)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.limit<1 or a.epochs<1:p.error("limit/epochs must be positive")
    for f in (a.level1,a.level2):
        if not f.exists():p.error(f"missing QA input: {f}")
    selected=combine(a.level1,a.level2,a.ledger,a.limit)
    report={"version":"v0.13.16","selected":len(selected),
            "level1":sum("EXPLICIT" in r.get("derivation","") for r in selected),
            "level2":sum("MENTION" in r.get("derivation","") for r in selected),
            "status":"DRY_RUN","production_unchanged":True}
    if not a.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    if not selected:p.error("no eligible pairs")
    if a.base.resolve()==a.candidate.resolve():p.error("cannot overwrite production")
    if not a.base.exists() or not a.tokenizer.exists():p.error("missing base or tokenizer")
    # Avoid claiming a new pilot when all pairs are already checkpoint-bound.
    trained=checkpoint_trained_fingerprints(a.base)
    selected=[r for r in selected if r["pair_fingerprint"] not in trained]
    if not selected:p.error("all chosen pairs already in base checkpoint")
    a.data.parent.mkdir(parents=True,exist_ok=True)
    a.data.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in selected),encoding="utf-8")
    cmd=[sys.executable,"online_train.py","--chat-data",str(a.data),
         "--base-model",str(a.base),"--tokenizer",str(a.tokenizer),
         "--output",str(a.candidate),"--state",str(a.state),
         "--epochs",str(a.epochs),"--learning-rate","0.000005"]
    result=subprocess.run(cmd,check=False)
    report.update(status="TRAINED_CANDIDATE" if result.returncode==0 and a.candidate.exists()
                  else "TRAINING_FAILED",trained_pairs=len(selected),returncode=result.returncode)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["status"]!="TRAINED_CANDIDATE":raise SystemExit(1)
if __name__=="__main__":main()
