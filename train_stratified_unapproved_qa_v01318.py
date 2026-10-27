"""v0.13.18: stratified and checkpoint-aware unapproved Semantic QA batch.

No production model change. A fingerprint means that a training pair was
recorded in a checkpoint; it does not prove the LLM can generate that knowledge.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from online_train import checkpoint_trained_fingerprints, pair_fingerprint
from unapproved_corpus_learning_v0139 import load_jsonl

DEFAULT_SUBJECTS=("始まり","時間","空間")

def build(level1,level2,ledger,checkpoint,subjects=DEFAULT_SUBJECTS,limit=16):
    if limit<len(subjects):raise ValueError("limit must allow one pair per subject")
    approvals={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    existing=checkpoint_trained_fingerprints(checkpoint)
    pool=[]
    seen=set()
    for path in (level1,level2):
        for row in load_jsonl(path):
            kid=row.get("knowledge_id")
            if not kid or approvals.get(kid,row.get("approval_state","UNAPPROVED"))=="REJECTED":continue
            q=str(row.get("user","")).strip()
            a=str(row.get("assistant","")).strip()
            if not q or not a:continue
            fp=pair_fingerprint(q,a)
            if fp in existing or fp in seen:continue
            seen.add(fp)
            pool.append({**row,"pair_fingerprint":fp,"source":"corpus-unapproved",
                         "approval_state":approvals.get(kid,"UNAPPROVED"),"truth_state":"UNVERIFIED"})
    selected=[]
    used=set()
    for subject in subjects:
        match=next((r for r in pool if r.get("subject")==subject and r["pair_fingerprint"] not in used),None)
        if match is None:raise ValueError(f"NO_UNTRAINED_QA_FOR_SUBJECT:{subject}")
        selected.append(match);used.add(match["pair_fingerprint"])
    for row in pool:
        if len(selected)>=limit:break
        if row["pair_fingerprint"] in used:continue
        selected.append(row);used.add(row["pair_fingerprint"])
    return selected

def binding_report(rows,checkpoint):
    trained=checkpoint_trained_fingerprints(checkpoint)
    return [{"knowledge_id":row["knowledge_id"],"subject":row.get("subject"),
             "pair_fingerprint":row["pair_fingerprint"],
             "checkpoint_bound":row["pair_fingerprint"] in trained,
             "approval_state":row["approval_state"],
             "truth_state":row["truth_state"]} for row in rows]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--level1",type=Path,default=Path("results/unapproved_semantic_qa_v01314.jsonl"))
    p.add_argument("--level2",type=Path,default=Path("results/unapproved_mention_qa_v01315.jsonl"))
    p.add_argument("--ledger",type=Path,default=Path("data/unapproved_corpus_ledger_v0139.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--candidate",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-qa-v01318.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_stratified_pairs_v01318.jsonl"))
    p.add_argument("--binding",type=Path,default=Path("results/unapproved_stratified_binding_v01318.json"))
    p.add_argument("--state",type=Path,default=Path("results/unapproved_stratified_state_v01318.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--epochs",type=int,default=1)
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.limit<3 or a.epochs<1:p.error("limit >= 3 and epochs >= 1 required")
    try:rows=build(a.level1,a.level2,a.ledger,a.base,limit=a.limit)
    except ValueError as exc:p.error(str(exc))
    result={"version":"v0.13.18","selected":len(rows),
            "subjects":{s:sum(r.get("subject")==s for r in rows) for s in DEFAULT_SUBJECTS},
            "status":"DRY_RUN","production_unchanged":True}
    if not a.run:
        print(json.dumps(result,ensure_ascii=False,indent=2));return
    if a.base.resolve()==a.candidate.resolve():p.error("candidate must differ from base")
    if not a.base.exists() or not a.tokenizer.exists():p.error("missing model/tokenizer")
    a.data.parent.mkdir(parents=True,exist_ok=True)
    a.data.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    cmd=[sys.executable,"online_train.py","--chat-data",str(a.data),
         "--base-model",str(a.base),"--tokenizer",str(a.tokenizer),
         "--output",str(a.candidate),"--state",str(a.state),
         "--epochs",str(a.epochs),"--learning-rate","0.000005"]
    result["exit_code"]=subprocess.run(cmd,check=False).returncode
    if result["exit_code"]!=0 or not a.candidate.exists():
        result["status"]="TRAINING_FAILED"
        print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(1)
    a.binding.parent.mkdir(parents=True,exist_ok=True)
    bindings=binding_report(rows,a.candidate)
    a.binding.write_text(json.dumps(bindings,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    result["status"]="TRAINED_CANDIDATE"
    result["checkpoint_bound_count"]=sum(r["checkpoint_bound"] for r in bindings)
    result["approval_status_modified"]=False
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
