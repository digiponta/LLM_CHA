"""v0.13.15 Level-2 mention-grounded QA, no synthetic definitions.

Examples: python prepare_unapproved_mention_qa_v01315.py --subjects 始まり 時間 空間
          python prepare_unapproved_mention_qa_v01315.py --subjects 始まり 時間 空間 --write
"""
import argparse
import json
from pathlib import Path
from unapproved_corpus_learning_v0139 import load_jsonl

QUEUE=Path("data/unapproved_corpus_train_queue_v0139.jsonl")
LEDGER=Path("data/unapproved_corpus_ledger_v0139.jsonl")
OUTPUT=Path("results/unapproved_mention_qa_v01315.jsonl")
DEFAULT_TERMS=("始まり","時間","空間")

def mention_qa(row,subject,approval_state):
    source_text=str(row.get("source_text","")).strip()
    if not subject or subject not in source_text:
        return None
    return {"user":f"未承認の原文で「{subject}」に言及した文章を示してください。",
            "assistant":"【未承認の記録・事実未検証】"+source_text,
            "subject":subject,"source_text":source_text,
            "knowledge_id":row["knowledge_id"],"source":row.get("source",""),
            "approval_state":approval_state,"truth_state":"UNVERIFIED",
            "derivation":"MENTION_ONLY_NOT_DEFINITION"}

def prepare(queue,ledger,subjects,limit):
    if limit<1:raise ValueError("limit must be positive")
    approvals={r["knowledge_id"]:r.get("approval_state","UNAPPROVED") for r in load_jsonl(ledger)}
    output=[]
    seen=set()
    for row in load_jsonl(queue):
        kid=row.get("knowledge_id")
        approval=approvals.get(kid,row.get("approval_state","UNAPPROVED"))
        if approval=="REJECTED":continue
        for subject in subjects:
            candidate=mention_qa(row,subject,approval)
            if candidate is None:continue
            key=(kid,subject)
            if key in seen:continue
            seen.add(key)
            output.append(candidate)
            if len(output)>=limit:return output
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queue",type=Path,default=QUEUE)
    p.add_argument("--ledger",type=Path,default=LEDGER)
    p.add_argument("--output",type=Path,default=OUTPUT)
    p.add_argument("--subjects",nargs="+",default=list(DEFAULT_TERMS))
    p.add_argument("--limit",type=int,default=200)
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    rows=prepare(a.queue,a.ledger,tuple(dict.fromkeys(a.subjects)),a.limit)
    result={"version":"v0.13.15","total_qa":len(rows),
            "by_subject":{term:sum(r["subject"]==term for r in rows) for term in a.subjects},
            "unique_knowledge_ids":len({r["knowledge_id"] for r in rows}),
            "write":a.write,"training_performed":False,
            "approval_status_modified":False,"output":str(a.output)}
    if a.write:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
