"""Evaluate frozen binding rules ONLY against explicitly human-reviewed source records."""
import argparse,json
from pathlib import Path
from evidence_cause_binding_v013588259 import answer_or_abstain

def validate_review(dataset,min_cases=5):
    cases=dataset.get("cases",[])
    if len(cases)<min_cases:return ["INSUFFICIENT_CASES"]
    errors=[]
    ids=set()
    for row in cases:
        id_=row.get("id")
        if not id_ or id_ in ids:errors.append("INVALID_OR_DUPLICATE_ID")
        ids.add(id_)
        r=row.get("review",{})
        if r.get("status")!="APPROVED_BY_HUMAN" or r.get("source_independent") is not True:
            errors.append("HUMAN_REVIEW_PENDING")
        if type(r.get("answerable")) is not bool:errors.append("ANSWERABILITY_NOT_ATTESTED")
        if r.get("answerable") is True and not str(r.get("required_substring") or "").strip():
            errors.append("ANSWER_VALUE_NOT_ATTESTED")
        ev=row.get("evidence",{})
        source=row.get("source",{})
        if ev.get("status")!="EVIDENCE" or not ev.get("excerpt") or not ev.get("url"):
            errors.append("INVALID_EVIDENCE")
        if source.get("excerpt_sha256") is None:errors.append("MISSING_SOURCE_HASH")
        if source.get("truncated"):errors.append("TRUNCATED_EXCERPT_REVIEW_REQUIRED")
        if not isinstance(r.get("reviewer_note"),str) or not r["reviewer_note"].strip():
            errors.append("REVIEW_NOTE_REQUIRED")
    return sorted(set(errors))

def evaluate(dataset,min_cases=5):
    reasons=validate_review(dataset,min_cases)
    if reasons:return {"status":"NOT_READY","reasons":reasons,"cases":len(dataset.get("cases",[])),
                      "production_changed":False}
    rows=[]
    for item in dataset["cases"]:
        decision=answer_or_abstain(item["question"],item["evidence"])
        accepted=decision["status"]=="BOUND_EXTRACT_ACCEPTED"
        truth=item["review"]
        required=truth.get("required_substring") or ""
        correct=bool(accepted and truth["answerable"] and required in str(decision.get("value",""))+str(decision.get("sentence","")))
        rows.append({"id":item["id"],"accepted":accepted,"correct_accept":correct,
                     "answerable":truth["answerable"],"status":decision["status"],
                     "selected_sentence":decision.get("sentence"),"value":decision.get("value"),
                     "source_url":item["evidence"]["url"]})
    positives=sum(x["answerable"] for x in rows); negatives=len(rows)-positives
    accepted=sum(x["accepted"] for x in rows); correct=sum(x["correct_accept"] for x in rows)
    negative_false=sum(x["accepted"] and not x["answerable"] for x in rows)
    return {"status":"HUMAN_REVIEWED_EVIDENCE_DIAGNOSTIC",
            "cases":len(rows),"positive_cases":positives,"negative_cases":negatives,
            "accepted":accepted,"correct_accept":correct,
            "false_accept":accepted-correct,"negative_false_accept":negative_false,
            "false_accept_rate":negative_false/negatives if negatives else None,
            "coverage":accepted/len(rows),
            "selective_accuracy":correct/accepted if accepted else None,
            "answerable_recall":correct/positives if positives else None,
            "results":rows,"production_changed":False,
            "caution":"Human-reviewed sample; statistical independence requires external auditing beyond the approval fields."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/wiki_evidence_review_v013588260.json")
    p.add_argument("--output",default="results/real_evidence_holdout_v013588260.json")
    p.add_argument("--min-cases",type=int,default=5)
    a=p.parse_args()
    result=evaluate(json.loads(Path(a.data).read_text(encoding="utf-8-sig")),a.min_cases)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in ("status","cases","reasons","accepted","false_accept_rate","coverage","selective_accuracy") if k in result},ensure_ascii=False))
    print("report:",path)
if __name__=="__main__":main()
