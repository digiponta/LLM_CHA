"""v0.4.25 incremental human annotation workflow (development data only).

Existing labels are joined by stable ID *and* exact capture contents.
A changed answer or score invalidates previous labels, preventing silent drift.
No inference, learning, Truth Gate, or Semantic Memory writes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from persona_quality_annotation_v0423 import FIELDS, load_jsonl, prepare
from persona_quality_benchmark_v0422 import score, validate

def reconcile(captures, prior_labels=(), annotations=()):
    prepared=prepare(captures)
    rows=prepared["rows"]
    by_id={r["id"]:r for r in rows}
    prior={}
    for labeled in prior_labels:
        validate(labeled)
        if labeled["split"]!="development" or labeled["label_source"]!="HUMAN_REVIEW":
            raise ValueError("prior labels must be reviewed development examples")
        key=labeled["id"]
        if key in prior:raise ValueError("duplicate prior id")
        prior[key]=labeled
    # Reject mismatched content even if the corresponding capture was excluded.
    for key,p in prior.items():
        if key not in by_id:raise ValueError("prior label has missing capture: "+key)
        current=by_id[key]
        if any(p[k]!=current[k] for k in FIELDS):
            raise ValueError("capture changed after human review: "+key)
    manual={}
    for a in annotations:
        if not isinstance(a,dict) or set(a)!={"id","gold_inappropriate","reviewer"}:
            raise ValueError("annotation schema")
        k=a["id"]
        if not isinstance(k,str) or not k or k in manual or k not in by_id:
            raise ValueError("invalid/duplicate annotation id")
        if type(a["gold_inappropriate"]) is not bool or not isinstance(a["reviewer"],str) or not a["reviewer"].strip():
            raise ValueError("invalid human label")
        manual[k]=a
    # Existing reviewed labels are immutable; conflicts require explicit separate adjudication.
    for key,a in manual.items():
        if key in prior and prior[key]["gold_inappropriate"]!=a["gold_inappropriate"]:
            raise ValueError("conflicting human labels: "+key)
    labeled=[];pending=[];reused=0
    for current in rows:
        k=current["id"]
        if k in prior:
            labeled.append(prior[k]);reused+=1
        elif k in manual:
            row={field:current[field] for field in FIELDS}
            row.update(split="development",gold_inappropriate=manual[k]["gold_inappropriate"],
                       label_source="HUMAN_REVIEW")
            labeled.append(row)
        else:
            pending.append(current)
    return {"version":"v0.4.25","captured":len(rows),
            "reused_labels":reused,"newly_labeled":len(labeled)-reused,
            "pending_count":len(pending),"pending":pending,"labeled":labeled,
            "independent_holdout_claimed":False}

def write_jsonl(path,rows):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows),
                 encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--captures",required=True)
    ap.add_argument("--prior")
    ap.add_argument("--annotations")
    ap.add_argument("--pending",required=True)
    ap.add_argument("--labeled",required=True)
    a=ap.parse_args()
    try:
        result=reconcile(load_jsonl(a.captures),
                         load_jsonl(a.prior) if a.prior else (),
                         load_jsonl(a.annotations) if a.annotations else ())
        write_jsonl(a.pending,[{"id":row["id"],"question":row["question"],
                                "answer":row["answer"],"gold_inappropriate":None}
                               for row in result["pending"]])
        write_jsonl(a.labeled,result["labeled"])
        stats=score(result["labeled"],split="development")
        print(json.dumps({k:v for k,v in result.items() if k not in ("pending","labeled")} |
                         {"benchmark":stats},ensure_ascii=False,indent=2))
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        ap.exit(1,f"annotation workflow failed: {exc}\n")
if __name__=="__main__":main()
