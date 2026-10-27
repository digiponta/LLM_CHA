"""v0.13.14 source-grounded, unapproved semantic QA preparation.

No inference of definitions from incidental mentions. No training or truth approval.
"""
import argparse
import json
import re
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl
from build_nagato_gain_probes_v10127 import SUBJECT_RE, STOP_SUBJECTS

DEFAULT_QUEUE=Path("data/unapproved_corpus_train_queue_v0139.jsonl")
DEFAULT_LEDGER=Path("data/unapproved_corpus_ledger_v0139.jsonl")
DEFAULT_OUTPUT=Path("results/unapproved_semantic_qa_v01314.jsonl")

def grounded_qa(row):
    statement=str(row.get("source_text","")).strip()
    match=SUBJECT_RE.match(statement)
    if not match:
        return None
    subject=match.group(1).strip()
    if subject in STOP_SUBJECTS or f"{subject}は" in STOP_SUBJECTS:
        return None
    if subject in {"これ","それ","あれ","ここ","そこ","今回","場合"}:
        return None
    return {"user":f"原文では「{subject}」について何と述べていますか",
            "assistant":"【未承認の記録】"+statement,
            "source":"corpus-unapproved",
            "knowledge_id":row["knowledge_id"],
            "subject":subject,
            "source_text":statement,
            "approval_state":"UNAPPROVED",
            "truth_state":"UNVERIFIED",
            "derivation":"EXPLICIT_SUBJECT_ONLY"}

def prepare(queue,ledger,limit,terms=()):
    approvals={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    output=[]
    for row in load_jsonl(queue):
        kid=row.get("knowledge_id")
        if approvals.get(kid,row.get("approval_state"))=="REJECTED":continue
        item=grounded_qa(row)
        if item is None:continue
        item["approval_state"]=approvals.get(kid,"UNAPPROVED")
        if terms and item["subject"] not in terms:continue
        output.append(item)
        if len(output)>=limit:break
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queue",type=Path,default=DEFAULT_QUEUE)
    p.add_argument("--ledger",type=Path,default=DEFAULT_LEDGER)
    p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    p.add_argument("--limit",type=int,default=100)
    p.add_argument("--subjects",nargs="*",default=[])
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    if a.limit<=0:p.error("--limit must be positive")
    rows=prepare(a.queue,a.ledger,a.limit,tuple(a.subjects))
    result={"qa_count":len(rows),"write":a.write,"output":str(a.output),
            "subjects":sorted({r["subject"] for r in rows}),
            "approval_status_modified":False,
            "training_performed":False}
    if a.write:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
