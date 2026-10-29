#!/usr/bin/env python3
"""v0.13.58.81: evidence-gated, label-blind answer reuse prototype.

An ACCEPT requires exact normalized question equality AND a separate explicit
source approval. Reviewed holdout labels never authorize an ACCEPT.
No dialogue runtime integration.
"""
import argparse,csv,json,re,unicodedata
from collections import Counter
from pathlib import Path
from answer_reuse_verifier_v0135880 import verify as baseline_verify

def normalize(s):
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",s or "")).strip("。！？?! ")

def decide(row,approved_sources):
    query=row.get("query","")
    candidate=row.get("candidate_question","")
    answer=row.get("candidate_answer","")
    source=row.get("source_id","")
    if not query.strip() or not candidate.strip() or not answer.strip():
        return "REJECT","EMPTY_FIELD"
    try:
        score=float(row.get("score","nan"))
    except ValueError:
        return "REJECT","INVALID_SCORE"
    import math
    if not math.isfinite(score) or score<0 or score>1:
        return "REJECT","INVALID_SCORE"
    base,reason=baseline_verify(query,candidate,answer,score)
    if reason in {"CURRENT_INFO","EXTERNAL_INPUT","ACTION_REQUIRED","MEDICAL_RISK",
                  "MEMORY_REQUIRED","CONTEXT_REQUIRED","ANSWER_UNCERTAIN"}:
        return "REVIEW",reason
    if normalize(query)!=normalize(candidate):
        return "REVIEW","NONEXACT_QUERY"
    if not source or source not in approved_sources:
        return "REVIEW","SOURCE_NOT_APPROVED"
    # Approved source identities must be maintained independently of heldout labels.
    return "ACCEPT","EXACT_QUERY_APPROVED_SOURCE"

def evaluate(rows,approved_sources):
    details=[];counts=Counter()
    for r in rows:
        decision,reason=decide(r,approved_sources)
        counts[decision]+=1
        label=r.get("answer_reusable","").strip().lower()
        if label in {"true","false"} and decision=="ACCEPT":
            counts["accepted_correct" if label=="true" else "accepted_incorrect"]+=1
        details.append({"query_id":r.get("query_id"),"candidate_id":r.get("candidate_id"),
                        "decision":decision,"reason":reason})
    return {"status":"PROVISIONAL_APPROVAL_GATED_REUSE","pairs":len(rows),
            "counts":dict(counts),
            "warning":"Approval lists must come from independent source review, never AI holdout labels. No runtime deployment or independent generalization claim.",
            "details":details}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--approved-sources",required=True,help="JSON object with approved_source_ids list, independently audited")
    p.add_argument("--output",default="results/answer_reuse_verifier_v0135881.json")
    a=p.parse_args()
    with open(a.input,encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    with open(a.approved_sources,encoding="utf-8-sig") as f:approval=json.load(f)
    if not isinstance(approval,dict) or not isinstance(approval.get("approved_source_ids"),list):
        raise ValueError("approved_source_ids must be an explicit list")
    approved=set(approval["approved_source_ids"])
    result=evaluate(rows,approved)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="details"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
