"""v0.13.10: Opt-in unapproved corpus micro-batch trainer.

Creates only a candidate checkpoint and separate training state, never changes
the currently used checkpoint, approval ledger, or chat learning log.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl

def build_batch(queue, ledger, output, limit=8):
    if limit<1 or limit>100:
        raise ValueError("limit must be 1..100")
    decisions={r["knowledge_id"]:r["approval_state"] for r in load_jsonl(ledger)}
    batch=[]
    seen=set()
    for row in load_jsonl(queue):
        key=row["knowledge_id"]
        if key in seen or decisions.get(key,row.get("approval_state"))=="REJECTED":
            continue
        if row.get("training_state")!="PENDING":
            continue
        text=str(row.get("source_text","")).strip()
        if len(text)<8:
            continue
        seen.add(key)
        # This is explicitly a text-continuation target, NOT a fact approval.
        batch.append({"user":"次の未検証テキストを続けてください: "+text[:24],
            "assistant":text,"source":"corpus-unapproved",
            "knowledge_id":key,"approval_state":decisions.get(key,"UNAPPROVED"),
            "truth_state":"UNVERIFIED"})
        if len(batch)>=limit:
            break
    if output is not None:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in batch),encoding="utf-8")
    return batch

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queue",type=Path,default=Path("data/unapproved_corpus_train_queue_v0139.jsonl"))
    p.add_argument("--ledger",type=Path,default=Path("data/unapproved_corpus_ledger_v0139.jsonl"))
    p.add_argument("--batch-file",type=Path,default=Path("data/unapproved_microbatch_v01310.jsonl"))
    p.add_argument("--limit",type=int,default=8)
    p.add_argument("--base-model",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--candidate-model",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-candidate.pt"))
    p.add_argument("--candidate-state",type=Path,default=Path("data/unapproved_candidate_learning_state_v01310.json"))
    p.add_argument("--train",action="store_true",help="Explicitly run experimental candidate training")
    args=p.parse_args()
    batch=build_batch(args.queue,args.ledger,args.batch_file,args.limit)
    print(json.dumps({"staged":len(batch),"candidate_model":str(args.candidate_model),
                      "training_requested":args.train,"approval_changed":False},ensure_ascii=False))
    if not args.train:
        return
    if len(batch)<2:
        raise SystemExit("At least two eligible text pairs are required.")
    if not args.base_model.is_file() or not args.tokenizer.is_file():
        raise SystemExit("Base model or tokenizer not found; no training attempted.")
    if args.candidate_model.resolve()==args.base_model.resolve():
        raise SystemExit("Candidate must differ from base model.")
    cmd=[sys.executable,"online_train.py","--chat-data",str(args.batch_file),
         "--base-model",str(args.base_model),"--tokenizer",str(args.tokenizer),
         "--output",str(args.candidate_model),"--state",str(args.candidate_state),
         "--epochs","1","--learning-rate","0.000005"]
    result=subprocess.run(cmd,check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
    print("[candidate training complete; not promoted; approval states unchanged]")

if __name__=="__main__":
    main()
