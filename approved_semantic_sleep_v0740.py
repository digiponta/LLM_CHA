"""v0.7.40: stage operationally APPROVED evidence for Trusted /sleep.

The source-approved ledger is separate from the historical Nagato Semantic
Memory, so startup regeneration cannot erase or silently blend approvals.
Only /sleep queues Trusted learning pairs; no model weights change here.
"""
import json
import os
import tempfile
from pathlib import Path
from dual_semantic_memory_v071 import read_store
from internalized_knowledge_v10100 import pair_fingerprint,load_trained_fingerprints

def _atomic_jsonl(path, rows):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,
                                         prefix=".approved-sync-",delete=False) as f:
            tmp=f.name
            for row in rows:
                f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

def _load_jsonl(path):
    p=Path(path)
    if not p.exists():return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]

def synchronize(approved_path, sync_path):
    """Idempotent source-preserving mirror. Reject conflicting same IDs."""
    approved=read_store(approved_path,"APPROVED")
    previous=_load_jsonl(sync_path)
    existing={row["id"]:row for row in previous}
    added=0
    for record in approved:
        ident=record["id"]
        if ident in existing:
            old=existing[ident]
            if (old["assistant"],old["question"],old["source_id"]) != (
                    record["answer"],record["question"],record["source_id"]):
                raise ValueError("approved id content changed; sync refused")
            continue
        # Source evidence is identified as "原文証拠：<subject> #<source digest>".
        # Other approved Candidate questions are kept verbatim.
        question=record["question"]
        if question.startswith("原文証拠：") and " #" in question:
            subject=question[len("原文証拠："):].rsplit(" #",1)[0]
            prompt=f"{subject}の原文記述は"
        else:
            prompt=question
        row={"id":ident,"question":record["question"],"assistant":record["answer"],
             "source_id":record["source_id"],"user":prompt,
             "fingerprint":pair_fingerprint(prompt,record["answer"]),
             "approval_state":"APPROVED",
             "truth_state":"UNVERIFIED",
             "semantic_origin":"reference-approved-v0.7.40"}
        existing[ident]=row
        added+=1
    if added:
        _atomic_jsonl(sync_path,list(existing.values()))
    return {"approved":len(approved),"synced":len(existing),"added":added}

def queue_approved(sync_path, learning_log_path, learning_state_path):
    """Queue or repair APPROVED sleep pairs; count outstanding untrained pairs."""
    rows=_load_jsonl(sync_path)
    trained=load_trained_fingerprints(learning_state_path)
    logpath=Path(learning_log_path)
    logrows=_load_jsonl(logpath)
    existing={}
    for index,row in enumerate(logrows):
        user=str(row.get("user","")).strip()
        answer=str(row.get("assistant","")).strip()
        if user and answer:
            existing[pair_fingerprint(user,answer)]=index
    queued=0
    repaired=0
    outstanding=0
    for row in rows:
        fp=row["fingerprint"]
        if fp in trained:
            continue
        outstanding+=1
        if fp in existing:
            old=logrows[existing[fp]]
            if old.get("source")=="reference-approved-semantic-sleep":
                old["source"]="semantic-sleep"
                repaired+=1
            continue
        logrows.append({"user":row["user"],"assistant":row["assistant"],
                        "source":"semantic-sleep",
                        "semantic_origin":row["semantic_origin"],
                        "approved_id":row["id"],"fingerprint":fp,
                        "truth_state":row["truth_state"]})
        existing[fp]=len(logrows)-1
        queued+=1
    if queued or repaired:
        _atomic_jsonl(logpath,logrows)
    return {"approved_records":len(rows),"queued":queued,
            "repaired":repaired,"outstanding":outstanding}
