"""v0.7.4 explicitly reviewed promotion; never copies experimental weights."""
import argparse
import json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory

def promote(approved,candidates,record_id,reviewer,evidence,decision,report_path=None):
    if decision!="APPROVE":
        raise ValueError("explicit decision APPROVE required")
    if not reviewer or not reviewer.strip() or not evidence or not evidence.strip():
        raise ValueError("reviewer and evidence required")
    if len(reviewer)>256 or len(evidence)>12000:
        raise ValueError("review metadata too large")
    if report_path and Path(report_path).resolve() in (Path(approved).resolve(),Path(candidates).resolve()):
        raise ValueError("audit path overlaps memory")
    mem=DualMemory(approved,candidates)
    if not any(r["id"]==record_id and r["status"]=="PENDING" for r in mem.candidates()):
        raise ValueError("pending candidate not found")
    # No change to model weights, only stores.
    promoted=mem.approve(record_id)
    audit={"version":"v0.7.4","action":"PROMOTE_KNOWLEDGE_ONLY",
        "record_id":record_id,"source_id":promoted["source_id"],
        "reviewer":reviewer.strip(),"evidence":evidence.strip(),"decision":decision,
        "adapter_promoted":False,"weight_copied":False}
    if report_path:
        p=Path(report_path)
        if p.resolve() in (Path(approved).resolve(),Path(candidates).resolve()):
            raise ValueError("audit path overlaps memory")
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("a",encoding="utf-8") as f:
            f.write(json.dumps(audit,ensure_ascii=False)+"\n")
    return audit

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--approved",default="data/approved_v071.jsonl")
    ap.add_argument("--candidates",default="data/candidates_v071.jsonl")
    ap.add_argument("--id",required=True)
    ap.add_argument("--reviewer",required=True)
    ap.add_argument("--evidence",required=True)
    ap.add_argument("--decision",required=True)
    ap.add_argument("--audit",default="results/promotion_audit_v074.jsonl")
    a=ap.parse_args()
    result=promote(a.approved,a.candidates,a.id,a.reviewer,a.evidence,a.decision,a.audit)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
