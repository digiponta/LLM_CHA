"""v0.13.10 isolated pilot for training unapproved corpus on the current LLM.

Dry-run is the default. --run invokes existing online_train.py with a
separate candidate checkpoint and training-state path. No production promotion.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl

QUEUE=Path("data/unapproved_corpus_train_queue_v0139.jsonl")
LEDGER=Path("data/unapproved_corpus_ledger_v0139.jsonl")
BATCH=Path("results/unapproved_pilot_pairs_v01310.jsonl")
OUTPUT=Path("model/model-gpu-v1.6.2-unapproved-pilot-v01310.pt")
STATE=Path("results/unapproved_pilot_state_v01310.json")

def build_batch(queue,ledger,limit):
    approvals={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    selected=[]
    for row in load_jsonl(queue):
        if len(selected)>=limit:break
        kid=row.get("knowledge_id")
        if approvals.get(kid,row.get("approval_state"))=="REJECTED":
            continue
        if row.get("training_state")!="PENDING":
            continue
        text=row.get("source_text","").strip()
        if not text:continue
        # A source-preserving objective: the original passage is the target.
        selected.append({"user":"次の未承認コーパスの原文を再現してください。",
                         "assistant":text,
                         "source":"corpus-unapproved",
                         "knowledge_id":kid,
                         "approval_state":approvals.get(kid,"UNAPPROVED"),
                         "truth_state":"UNVERIFIED"})
    return selected

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queue",type=Path,default=QUEUE)
    p.add_argument("--ledger",type=Path,default=LEDGER)
    p.add_argument("--batch-file",type=Path,default=BATCH)
    p.add_argument("--output",type=Path,default=OUTPUT)
    p.add_argument("--state",type=Path,default=STATE)
    p.add_argument("--base-model",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--epochs",type=int,default=1)
    p.add_argument("--run",action="store_true")
    args=p.parse_args()
    if args.limit<=0 or args.epochs<=0:p.error("limit and epochs must be positive")
    rows=build_batch(args.queue,args.ledger,args.limit)
    report={"selected":len(rows),"candidate_checkpoint":str(args.output),"run":args.run,
            "production_unchanged":True,"approval_state_modified":False}
    if not rows:
        print(json.dumps({**report,"status":"NO_ELIGIBLE_ROWS"},ensure_ascii=False,indent=2))
        return
    if not args.run:
        print(json.dumps({**report,"status":"DRY_RUN"},ensure_ascii=False,indent=2))
        return
    if args.output.resolve()==args.base_model.resolve():
        p.error("candidate output must differ from base model")
    if not args.base_model.exists() or not args.tokenizer.exists():
        p.error("base model or tokenizer not found")
    args.batch_file.parent.mkdir(parents=True,exist_ok=True)
    args.batch_file.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows),encoding="utf-8")
    command=[sys.executable,"online_train.py","--chat-data",str(args.batch_file),
             "--base-model",str(args.base_model),"--tokenizer",str(args.tokenizer),
             "--output",str(args.output),"--state",str(args.state),
             "--epochs",str(args.epochs),"--learning-rate","0.000005"]
    result=subprocess.run(command,check=False)
    report.update(status="TRAINED_CANDIDATE" if result.returncode==0 and args.output.exists()
                  else "TRAINING_FAILED",exit_code=result.returncode)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["status"]!="TRAINED_CANDIDATE":raise SystemExit(1)

if __name__=="__main__":main()
