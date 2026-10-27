"""v0.13.9: Source-preserving unapproved corpus training preparation.

Does not change truth records, approvals, model weights, or legacy /sleep.
Run: python unapproved_corpus_learning_v0139.py --status
     python unapproved_corpus_learning_v0139.py --prepare --limit 100
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

DEFAULT_SOURCE=Path("data/data-nagato.txt")
DEFAULT_LEDGER=Path("data/unapproved_corpus_ledger_v0139.jsonl")
DEFAULT_QUEUE=Path("data/unapproved_corpus_train_queue_v0139.jsonl")

def source_segments(text):
    # Preserve original sentences, including non-subject-keyed material.
    for block in re.split(r"(?<=[。！？!?])\s*|[\r\n]+",text):
        sentence=block.strip()
        if sentence:
            yield sentence

def knowledge_id(sentence):
    return "raw-"+hashlib.sha256(sentence.encode("utf-8")).hexdigest()[:24]

def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

def corpus_rows(source):
    text=source.read_text(encoding="utf-8-sig")
    seen=set()
    result=[]
    for text_piece in source_segments(text):
        key=knowledge_id(text_piece)
        if key in seen:
            continue
        seen.add(key)
        result.append({"knowledge_id":key,"source_text":text_piece,
                       "source":source.as_posix(),"approval_state":"UNAPPROVED",
                       "truth_state":"UNVERIFIED"})
    return result

def plan(source=DEFAULT_SOURCE, ledger=DEFAULT_LEDGER, queue=DEFAULT_QUEUE, limit=100, write=False):
    rows=corpus_rows(source)
    previous={r["knowledge_id"]:r for r in load_jsonl(ledger)}
    queued_ids={r["knowledge_id"] for r in load_jsonl(queue)}
    # Existing human decisions take precedence. Never reset APPROVED or REJECTED.
    merged=[]
    new=[]
    for row in rows:
        existing=previous.get(row["knowledge_id"])
        if existing:
            row={**row,**existing}
        merged.append(row)
        if row["approval_state"]!="REJECTED" and row["knowledge_id"] not in queued_ids:
            new.append(row)
    batch=new[:limit]
    if write:
        ledger.parent.mkdir(parents=True,exist_ok=True)
        ledger.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in merged),encoding="utf-8")
        queue.parent.mkdir(parents=True,exist_ok=True)
        with queue.open("a",encoding="utf-8") as f:
            for row in batch:
                f.write(json.dumps({"knowledge_id":row["knowledge_id"],
                   "source":row["source"],"source_text":row["source_text"],
                   "approval_state":row["approval_state"],
                   "truth_state":row["truth_state"],
                   "training_state":"PENDING"},ensure_ascii=False)+"\n")
    return {"source_segments":len(rows),"already_queued":len(queued_ids),
            "eligible_new":len(new),"batch":len(batch),"write":write,
            "approved":sum(r["approval_state"]=="APPROVED" for r in merged),
            "rejected":sum(r["approval_state"]=="REJECTED" for r in merged)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=DEFAULT_SOURCE)
    p.add_argument("--ledger",type=Path,default=DEFAULT_LEDGER)
    p.add_argument("--queue",type=Path,default=DEFAULT_QUEUE)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--status",action="store_true")
    group.add_argument("--prepare",action="store_true")
    p.add_argument("--limit",type=int,default=100)
    args=p.parse_args()
    if args.limit<0:p.error("--limit must be nonnegative")
    print(json.dumps(plan(args.source,args.ledger,args.queue,args.limit,args.prepare),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
