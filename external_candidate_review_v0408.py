"""v0.4.8 — explicit human review of isolated Wikipedia research candidates.

Review approval is not factual verification, Semantic Memory promotion or training.
Single-writer CLI; no concurrent access protection.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from external_candidate_store_v0407 import _store, _atomic_write

DECISIONS={"APPROVED_FOR_REVIEW_ONLY","REJECTED","PENDING_REVIEW"}
MAX_AUDITS=50

def review(store_path, candidate_id, expected_sha256, decision, reviewer, reason):
    for name,value,limit in (("candidate_id",candidate_id,24),
                              ("content_sha256",expected_sha256,64),
                              ("reviewer",reviewer,100),
                              ("reason",reason,1000)):
        if not isinstance(value,str) or not value.strip() or len(value)>limit:
            raise ValueError("invalid "+name)
    if len(candidate_id)!=24 or any(c not in "0123456789abcdef" for c in candidate_id):
        raise ValueError("invalid candidate id")
    if len(expected_sha256)!=64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise ValueError("invalid content sha256")
    if decision not in DECISIONS:raise ValueError("invalid decision")
    if not Path(store_path).is_file():raise ValueError("candidate store does not exist")
    db=_store(store_path)
    records=[r for r in db["records"] if r["id"]==candidate_id]
    if len(records)!=1:raise ValueError("candidate not found")
    row=records[0]
    if row.get("content_sha256")!=expected_sha256:
        raise ValueError("candidate content changed: review requires current SHA256")
    if row.get("review_state") not in ("PENDING_REVIEW","NEEDS_REREVIEW","APPROVED_FOR_REVIEW_ONLY","REJECTED"):
        raise ValueError("invalid current review state")
    audits=row.setdefault("review_audit",[])
    if not isinstance(audits,list) or len(audits)>=MAX_AUDITS:
        raise ValueError("review audit limit reached")
    old=row["review_state"]
    now=datetime.now(timezone.utc).isoformat()
    audits.append({"reviewer":reviewer.strip(),"reason":reason.strip(),
                   "decision":decision,"previous_state":old,
                   "content_sha256":expected_sha256,"reviewed_at_utc":now,
                   "article_url":row["url"],"candidate_id":candidate_id})
    row["review_state"]=decision
    row["factual_truth"]="UNVERIFIED"
    row["eligible_for_training"]=False
    _atomic_write(store_path,db)
    return {"version":"v0.4.8","candidate_id":candidate_id,
            "previous_state":old,"review_state":decision,
            "reviewed_at_utc":now,"reviewer":reviewer.strip(),
            "content_sha256":expected_sha256,"article_url":row["url"],
            "truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False}

def list_candidates(store_path):
    db=_store(store_path)
    return [{"id":r["id"],"concept":r.get("concept"),"title":r.get("title"),
             "url":r.get("url"),"content_sha256":r.get("content_sha256"),
             "review_state":r.get("review_state"),
             "review_count":len(r.get("review_audit",[]))}
            for r in db["records"]]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--store",default="results/external_candidate_store_v0407.json")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("list")
    r=sub.add_parser("review")
    r.add_argument("--id",required=True)
    r.add_argument("--sha256",required=True)
    r.add_argument("--decision",choices=sorted(DECISIONS),required=True)
    r.add_argument("--reviewer",required=True)
    r.add_argument("--reason",required=True)
    a=p.parse_args()
    try:
        if a.command=="list":
            if not Path(a.store).is_file():raise ValueError("candidate store does not exist")
            result={"version":"v0.4.8","candidates":list_candidates(a.store)}
        else:
            result=review(a.store,a.id,a.sha256,a.decision,a.reviewer,a.reason)
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        p.exit(1,f"External review failed: {type(exc).__name__}: {exc}\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
