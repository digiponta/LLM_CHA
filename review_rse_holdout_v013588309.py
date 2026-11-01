"""Create and validate a separate human-review label file for RSE test-split cases.

Never alter the immutable test sampling report. Empty labels remain pending.
"""
import argparse,json
from pathlib import Path
FIELDS=("intent_match","slot_match","answer_suitable","persona_transfer_risk")
def template(holdout):
    return {"format":"rse-human-review-v1","source_split":holdout["split"],
            "review_instructions":"For each case, independently formulate a new user query and review original answer locally. Do not copy private text into shared reports.",
            "cases":[{"id":x["id"],"dialogue_id":x["dialogue_id"],
                      "new_query":None,**{f:None for f in FIELDS},
                      "reviewer_note":None} for x in holdout["cases"]]}
def validate(holdout,review):
    reference={x["id"]:x["dialogue_id"] for x in holdout["cases"]}
    errors=[];seen=set();complete=0;positives=0;negatives=0
    for x in review.get("cases",[]):
        k=x.get("id")
        if k not in reference:errors.append("UNKNOWN_CASE_ID");continue
        if k in seen:errors.append("DUPLICATE_CASE_ID")
        seen.add(k)
        if x.get("dialogue_id")!=reference[k]:errors.append("DIALOGUE_ID_MISMATCH")
        fields=[x.get(f) for f in FIELDS]
        if any(v is not None and type(v) is not bool for v in fields):errors.append("INVALID_BOOLEAN_LABEL")
        q=x.get("new_query")
        if q is not None and (not isinstance(q,str) or not q.strip()):errors.append("INVALID_QUERY")
        if q and all(type(v) is bool for v in fields):
            complete+=1
            if x["answer_suitable"] and not x["persona_transfer_risk"]:positives+=1
            else:negatives+=1
    if seen!=set(reference):errors.append("MISSING_CASE_IDS")
    return {"status":"INVALID" if errors else "LABELING_COMPLETE" if complete==len(reference) else "HUMAN_LABELING_PENDING",
            "total":len(reference),"fully_labeled":complete,"pending":len(reference)-complete,
            "reviewed_reusable":positives,"reviewed_unsuitable_or_persona_risk":negatives,
            "errors":sorted(set(errors)),"independent_human_verification_attested":False,
            "gate_accuracy_evaluated":False}
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--holdout",default="results/rse_independent_holdout_v013588308.json")
    p.add_argument("--review",default="results/rse_human_review_v013588309.json")
    p.add_argument("--init",action="store_true")
    p.add_argument("--report",default="results/rse_human_review_status_v013588309.json")
    a=p.parse_args()
    holdout=read(a.holdout);path=Path(a.review)
    if a.init:
        if path.exists():raise SystemExit("Review already exists; refusing overwrite")
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(template(holdout),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if not path.exists():raise SystemExit("Review missing: run --init")
    result=validate(holdout,read(path))
    out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["status"]=="INVALID":raise SystemExit(2)
if __name__=="__main__":main()
