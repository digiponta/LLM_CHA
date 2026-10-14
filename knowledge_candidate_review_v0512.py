"""v0.5.12 cautious review lifecycle for user-taught candidate memory.

Review approval is NOT independent truth verification and does not authorize
model training, /sleep, or promotion to trusted Semantic Memory.
"""
import json
from pathlib import Path
from conversation_resource_memory_v042866 import write_json_atomic

def _read(path):
    p=Path(path)
    if not p.exists():return []
    rows=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(rows,list):raise ValueError("invalid candidate store")
    return rows

def inspect(path,concept):
    rows=_read(path)
    selected=[(i,r) for i,r in enumerate(rows,1) if r.get("concept")==concept]
    variants={r.get("user_explanation","").strip() for _,r in selected}
    variants.discard("")
    conflict=len(variants)>1
    return {"concept":concept,"possible_conflict":conflict,
       "note":"Different descriptions need human review; not proof of contradiction" if conflict else "No differing description in candidate store",
       "candidates":[{"id":i,"explanation":r.get("user_explanation"),
          "status":r.get("status"),"truth_state":r.get("truth_state"),
          "source":r.get("source"),"verified":r.get("verified",False),
          "train_ready":r.get("train_ready",False)} for i,r in selected]}

def approve(path,candidate_id):
    if type(candidate_id) is not int or candidate_id<1:raise ValueError("invalid candidate ID")
    rows=_read(path)
    if candidate_id>len(rows):raise ValueError("candidate ID not found")
    target=rows[candidate_id-1]
    if target.get("truth_state")!="USER_REPORTED_UNVERIFIED":
        raise ValueError("unsupported truth state")
    if target.get("status") not in ("PENDING_REVIEW","REVIEW_ACKNOWLEDGED"):
        raise ValueError("candidate is not reviewable")
    target["status"]="REVIEW_ACKNOWLEDGED"
    target["reviewer_acknowledged"]=True
    target["verified"]=False
    target["fact_promoted"]=False
    target["train_ready"]=False
    target["approved_for_sleep"]=False
    write_json_atomic(rows,path)
    return {"id":candidate_id,"status":target["status"],
        "verified":False,"fact_promoted":False,"train_ready":False,
        "approved_for_sleep":False,
        "message":"Review acknowledged only; verification and promotion are separate."}
