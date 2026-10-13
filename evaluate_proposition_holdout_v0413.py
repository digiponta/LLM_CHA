"""v0.4.13 frozen post-development evaluation (not blind external holdout)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from article_proposition_alignment_v0410 import align as baseline
from article_proposition_alignment_v0412 import align as expanded
from external_candidate_store_v0407 import _atomic_write

FIXTURE=Path(__file__).resolve().parent/"data/proposition_holdout_v0413.json"

def evidence(row):
    text=row["text"]
    return {"version":"v0.4.9","candidate_id":"fixture-"+row["id"],
            "candidate_content_sha256":"0"*64,"concept":row["concept"],
            "article_title":row["concept"],
            "article_url":"https://ja.wikipedia.org/wiki/fixture",
            "extract_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "lead_extract":text,"pageid":1,"revid":1,
            "factual_truth":"UNVERIFIED","eligible_for_training":False,
            "revision_content_verified":False}

def score(cases,aligner):
    tp=fp=fn=tn=0;detail=[]
    for row in cases:
        result=aligner(evidence(row))
        predicted=result["proposition_count"]>0
        expected=row["expected_extract"]
        for p in result["propositions"]:
            if row["text"][p["evidence_start"]:p["evidence_end"]]!=p["evidence_text"]:
                raise ValueError("invalid evidence span: "+row["id"])
            if p["factual_truth"]!="UNVERIFIED" or p["eligible_for_training"] is not False:
                raise ValueError("unsafe proposition: "+row["id"])
        if expected and predicted:tp+=1
        elif not expected and predicted:fp+=1
        elif expected:fn+=1
        else:tn+=1
        detail.append({"id":row["id"],"category":row["category"],"concept":row["concept"],
                       "expected":expected,"predicted":predicted,"match":expected==predicted,
                       "proposition_count":result["proposition_count"]})
    return {"total":len(cases),"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn) if tp+fn else None,
            "specificity":tn/(tn+fp) if tn+fp else None,
            "balanced_accuracy":((tp/(tp+fn))+(tn/(tn+fp)))/2 if (tp+fn) and (tn+fp) else None,
            "details":detail}

def evaluate(path=FIXTURE):
    file=Path(path)
    if file.stat().st_size>128_000:raise ValueError("oversized fixture")
    raw=file.read_bytes()
    payload=json.loads(raw.decode("utf-8"))
    if payload.get("version")!="v0.4.13" or payload.get("independent_blind") is not False:
        raise ValueError("wrong fixture schema")
    cases=payload.get("cases")
    if not isinstance(cases,list) or len(cases)<20:raise ValueError("insufficient cases")
    ids=[]
    for row in cases:
        if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k] for k in ("id","concept","text","category")):
            raise ValueError("malformed case")
        if type(row.get("expected_extract")) is not bool:raise ValueError("missing expected label")
        ids.append(row["id"])
    if len(ids)!=len(set(ids)):raise ValueError("duplicate case")
    return {"version":"v0.4.13",
            "protocol":"POST_DEVELOPMENT_FROZEN_HAND_AUTHORED_NOT_EXTERNAL_BLIND_HOLDOUT",
            "fixture_sha256":hashlib.sha256(raw).hexdigest(),
            "case_count":len(cases),
            "baseline_v0410":score(cases,baseline),
            "expanded_v0412":score(cases,expanded),
            "truth_promotions":0,"semantic_memory_writes":0,"training_enabled":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",default=str(FIXTURE))
    p.add_argument("--report")
    args=p.parse_args()
    try:
        report=evaluate(args.fixture)
        if args.report:
            if Path(args.report).resolve()==Path(args.fixture).resolve():raise ValueError("cannot overwrite fixture")
            _atomic_write(args.report,report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except (ValueError,OSError,UnicodeError,TypeError,KeyError,json.JSONDecodeError) as exc:
        p.exit(1,f"v0.4.13 evaluation failed: {type(exc).__name__}: {exc}\n")
if __name__=="__main__":main()
