"""v0.7.1: separate approved and candidate knowledge stores.

A candidate can never be read as approved without explicit, source-preserving
promotion. No model weights, production Semantic Memory or /sleep are changed.
"""
import json
import os
import tempfile
import hashlib
from pathlib import Path

SCHEMA="llm-cha-dual-memory-v0.7.1"
STATES={"PENDING","REJECTED","APPROVED"}
def fingerprint(question,answer):
    return hashlib.sha256((question.strip()+"\n"+answer.strip()).encode("utf-8")).hexdigest()

def validate(row):
    if not isinstance(row,dict):
        raise ValueError("record must be dict")
    required={"id","question","answer","source_id","status"}
    if not required.issubset(row) or any(not isinstance(row[k],str) for k in required):
        raise ValueError("invalid knowledge record")
    if not all(row[k].strip() for k in ("id","question","answer","source_id")):
        raise ValueError("empty knowledge fields")
    if row["status"] not in STATES:
        raise ValueError("invalid approval status")
    if any(len(row[k])>12000 for k in required):
        raise ValueError("oversized knowledge fields")
    return dict(row)

def read_store(path,expected_status=None):
    p=Path(path)
    if not p.exists():
        return []
    records=[]
    ids=set()
    for i,line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():continue
        r=validate(json.loads(line))
        if expected_status and r["status"] != expected_status:
            raise ValueError(f"{p}:{i}: wrong status for store")
        if r["id"] in ids:
            raise ValueError(f"{p}:{i}: duplicate id")
        ids.add(r["id"])
        records.append(r)
    return records

def write_store(path,rows,expected_status=None):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    verified=[validate(r) for r in rows]
    if len({r["id"] for r in verified})!=len(verified):
        raise ValueError("duplicate IDs")
    if expected_status and any(r["status"]!=expected_status for r in verified):
        raise ValueError("status mismatch")
    tmp=None
    try:
        with tempfile.NamedTemporaryFile("w",dir=p.parent,encoding="utf-8",delete=False,prefix=".dual-memory-",suffix=".tmp") as f:
            tmp=f.name
            for row in verified:
                f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if tmp and os.path.exists(tmp):os.unlink(tmp)

class DualMemory:
    def __init__(self,approved_path,candidate_path):
        self.approved_path=Path(approved_path)
        self.candidate_path=Path(candidate_path)
    def candidates(self):
        return read_store(self.candidate_path)
    def approved(self):
        return read_store(self.approved_path,"APPROVED")
    def propose(self,question,answer,source_id):
        row={"id":fingerprint(question,answer),"question":question.strip(),"answer":answer.strip(),
             "source_id":source_id,"status":"PENDING"}
        validate(row)
        pending=self.candidates()
        if any(r["id"]==row["id"] for r in pending) or any(r["id"]==row["id"] for r in self.approved()):
            return row["id"]
        pending.append(row)
        write_store(self.candidate_path,pending)
        return row["id"]
    def approve(self,record_id):
        candidates=self.candidates()
        approved=self.approved()
        target=next((r for r in candidates if r["id"]==record_id and r["status"]=="PENDING"),None)
        if target is None:
            raise ValueError("pending candidate not found")
        if any(r["question"]==target["question"] and r["answer"]!=target["answer"] for r in approved):
            raise ValueError("conflicting approved answer")
        promotion=dict(target,status="APPROVED")
        if not any(r["id"]==promotion["id"] for r in approved):
            # Write approved before deleting candidate: interrupted promotion
            # may leave a duplicate, but never silently lose approved data.
            write_store(self.approved_path,approved+[promotion],"APPROVED")
        write_store(self.candidate_path,[r for r in candidates if r["id"]!=record_id])
        return promotion
    def reject(self,record_id):
        candidates=self.candidates()
        row=next((r for r in candidates if r["id"]==record_id and r["status"]=="PENDING"),None)
        if row is None:raise ValueError("pending candidate not found")
        updated=[dict(r,status="REJECTED") if r["id"]==record_id else r for r in candidates]
        write_store(self.candidate_path,updated)
        return record_id
    def lookup_approved(self,question):
        matches=[r for r in self.approved() if r["question"]==question.strip()]
        if not matches:return None
        if len({r["answer"] for r in matches})!=1:raise ValueError("ambiguous approved answer")
        return matches[0]
