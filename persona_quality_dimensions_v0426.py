"""v0.4.26 multi-dimensional, human-only response quality diagnosis.

Evaluation-only; never changes binary labels or the runtime response.
Grounding can be NOT_APPLICABLE when no factual evidence is requested.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from persona_quality_benchmark_v0422 import load_jsonl, score

AXES=("relevance","fluency","persona_consistency","grounding")
VALUES={"PASS","FAIL","UNCERTAIN","NOT_APPLICABLE"}
FIELDS={"id","reviewer",*AXES}
MAX_BYTES=2_000_000

def evaluate_dimensions(binary_rows, dimension_rows):
    by_id={}
    for r in binary_rows:
        if r["id"] in by_id:raise ValueError("duplicate binary id")
        by_id[r["id"]]=r
    reviews={}
    for r in dimension_rows:
        if not isinstance(r,dict) or set(r)!=FIELDS:raise ValueError("dimension schema")
        key=r["id"]
        if not isinstance(key,str) or not key or key not in by_id or key in reviews:
            raise ValueError("unknown/duplicate dimension id")
        if not isinstance(r["reviewer"],str) or not r["reviewer"].strip():
            raise ValueError("human reviewer required")
        for axis in AXES:
            if r[axis] not in VALUES:raise ValueError("invalid "+axis)
            if axis in ("relevance","fluency") and r[axis]=="NOT_APPLICABLE":
                raise ValueError("core axis cannot be not applicable")
        reviews[key]=r
    counts={a:{v:0 for v in sorted(VALUES)} for a in AXES}
    cross={"inappropriate":0,"appropriate":0,"inappropriate_with_no_axis_fail":0,
           "appropriate_with_axis_fail":0}
    for key,r in reviews.items():
        b=by_id[key]["gold_inappropriate"]
        cross["inappropriate" if b else "appropriate"]+=1
        failing=any(r[a]=="FAIL" for a in AXES)
        if b and not failing:cross["inappropriate_with_no_axis_fail"]+=1
        if not b and failing:cross["appropriate_with_axis_fail"]+=1
        for a in AXES:counts[a][r[a]]+=1
    return {"version":"v0.4.26","status":"EVALUATED" if reviews else "NO_DIMENSION_LABELS",
            "binary_total":len(by_id),"reviewed_count":len(reviews),
            "pending_ids":[i for i in by_id if i not in reviews],
            "axis_counts":counts,"binary_dimension_disagreements":cross,
            "independent_holdout_claimed":False,
            "runtime_decisions_modified":False,"training_enabled":False}

def read_dimensions(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>MAX_BYTES:raise ValueError("invalid dimensions file")
    return [json.loads(x) for x in p.read_text(encoding="utf-8-sig").splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--labeled",required=True)
    ap.add_argument("--dimensions")
    ap.add_argument("--pending",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    try:
        binary=load_jsonl(args.labeled)
        if any(x["split"]!="development" for x in binary):
            raise ValueError("development-only multidimensional study")
        dims=read_dimensions(args.dimensions) if args.dimensions else []
        result=evaluate_dimensions(binary,dims)
        pending=[{"id":r["id"],"question":r["question"],"answer":r["answer"],
                  "gold_inappropriate":r["gold_inappropriate"],
                  "relevance":None,"fluency":None,"persona_consistency":None,"grounding":None}
                 for r in binary if r["id"] in result["pending_ids"]]
        for path,data in ((args.pending,"".join(json.dumps(x,ensure_ascii=False)+"\n" for x in pending)),
                          (args.report,json.dumps(result,ensure_ascii=False,indent=2)+"\n")):
            p=Path(path)
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(data,encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        ap.exit(1,f"dimensional evaluation failed: {exc}\n")
if __name__=="__main__":main()
