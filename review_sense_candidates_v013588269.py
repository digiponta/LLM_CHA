"""Explicit human review and isolated semantic-memory staging.

This module never writes to the live proposition or unified-memory stores.
"""
import argparse
import json
from pathlib import Path

DECISIONS={"APPROVE","REJECT","DEFER"}

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def record_decision(report,candidate_id,decision,reviewer,note,prior=None):
    decision=str(decision).upper()
    if decision not in DECISIONS:
        raise ValueError("INVALID_DECISION")
    if not str(reviewer).strip() or not str(note).strip():
        raise ValueError("REVIEWER_AND_NOTE_REQUIRED")
    candidates=[c for c in report.get("candidates",[]) if c.get("id")==candidate_id]
    if len(candidates)!=1:
        raise ValueError("CANDIDATE_NOT_UNIQUE")
    candidate=candidates[0]
    if decision=="APPROVE" and candidate.get("review_status") in ("POSSIBLE_CONFLICT","POSSIBLE_DUPLICATE"):
        raise ValueError("UNRESOLVED_DUPLICATE_OR_CONFLICT")
    reviews=dict(prior or {})
    if candidate_id in reviews and reviews[candidate_id].get("decision")!=decision:
        raise ValueError("DECISION_CHANGE_REQUIRES_SEPARATE_REVIEW")
    reviews[candidate_id]={
        "candidate_id":candidate_id,
        "decision":decision,
        "reviewer":str(reviewer).strip(),
        "note":str(note).strip(),
        "source_case_id":candidate.get("source_case_id"),
        "subject":candidate.get("subject"),
        "meaning":candidate.get("meaning"),
        "evidence_sentence":candidate.get("evidence_sentence"),
        "source_url":candidate.get("source_url"),
        "source_trust":"EXTERNAL_UNVERIFIED",
        "human_review_recorded":True,
        "production_promoted":False,
    }
    return reviews

def stage(report,reviews):
    candidates={c["id"]:c for c in report.get("candidates",[])}
    staged=[]
    for cid,review in reviews.items():
        if review.get("decision")!="APPROVE":continue
        c=candidates.get(cid)
        if c is None or c.get("review_status") in ("POSSIBLE_CONFLICT","POSSIBLE_DUPLICATE"):
            continue
        if review.get("subject")!=c.get("subject") or review.get("meaning")!=c.get("meaning"):
            continue
        if review.get("evidence_sentence")!=c.get("evidence_sentence"):
            continue
        staged.append({"id":cid,"subject":c["subject"],"sense":cid,
                       "relation":"definition","value":c["meaning"],
                       "evidence":c["evidence_sentence"],"source_url":c["source_url"],
                       "human_reviewed":True,"external_truth_verified":False,
                       "production_promoted":False})
    return {"status":"STAGED_FOR_SEMANTIC_REVIEW","count":len(staged),
            "entries":staged,"live_memory_changed":False,"model_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",default="results/sense_discovery_v013588268_fixed.json")
    p.add_argument("--reviews",default="data/sense_human_reviews_v013588269.json")
    p.add_argument("--candidate")
    p.add_argument("--decision",choices=sorted(DECISIONS))
    p.add_argument("--reviewer")
    p.add_argument("--note")
    p.add_argument("--stage-output",default="results/sense_approved_staging_v013588269.json")
    args=p.parse_args()
    report=load_json(args.report)
    path=Path(args.reviews)
    reviews=load_json(path) if path.exists() else {}
    if args.candidate:
        if not args.decision:
            raise ValueError("DECISION_REQUIRED")
        reviews=record_decision(report,args.candidate,args.decision,args.reviewer,args.note,reviews)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    elif any(x is not None for x in (args.decision,args.reviewer,args.note)):
        raise ValueError("CANDIDATE_REQUIRED")
    staged=stage(report,reviews)
    output=Path(args.stage_output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(staged,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":staged["status"],"candidate_count":len(report.get("candidates",[])),
        "reviewed_count":len(reviews),"staged_count":staged["count"],
        "production_changed":False,"report":str(output)},ensure_ascii=False))

if __name__=="__main__":
    main()
