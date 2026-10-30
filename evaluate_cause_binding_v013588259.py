"""Measure false acceptance, coverage and selective correctness on explicit cases.

Synthetic fixture metrics are diagnostic, not held-out generalization estimates.
"""
import argparse
import json
from pathlib import Path
from evidence_cause_binding_v013588259 import answer_or_abstain

def evaluate(cases):
    results=[]
    for item in cases:
        got=answer_or_abstain(item["question"],item["evidence"])
        accepted=got["status"]=="BOUND_EXTRACT_ACCEPTED"
        expected=item["expected"]
        required=expected.get("required_substring")
        valid=bool(accepted and expected["answerable"] and
                   (not required or required in str(got.get("value","")) or required in str(got.get("sentence",""))))
        false_accept=bool(accepted and not valid)
        results.append({"id":item["id"],"question":item["question"],
                        "expected_answerable":expected["answerable"],
                        "status":got["status"],"accepted":accepted,
                        "correct_accept":valid,"false_accept":false_accept,
                        "value":got.get("value"),"sentence":got.get("sentence")})
    positives=sum(x["expected_answerable"] for x in results)
    negatives=len(results)-positives
    accepted=sum(x["accepted"] for x in results)
    correct=sum(x["correct_accept"] for x in results)
    false=sum(x["false_accept"] for x in results)
    negative_false=sum(x["accepted"] and not x["expected_answerable"] for x in results)
    false_negative=sum(x["expected_answerable"] and not x["accepted"] for x in results)
    return {"status":"BINDING_EVAL_DIAGNOSTIC","cases":len(results),
        "positive_cases":positives,"negative_cases":negatives,
        "accepted":accepted,"correct_accept":correct,"false_accept":false,"negative_false_accept":negative_false,
        "false_negative":false_negative,
        "false_accept_rate":negative_false/negatives if negatives else None,
        "accepted_error_rate":false/accepted if accepted else None,
        "coverage":accepted/len(results) if results else None,
        "answerable_recall":correct/positives if positives else None,
        "selective_accuracy":correct/accepted if accepted else None,
        "results":results,
        "caution":"Synthetic fixtures, not independent statistical holdout. Error on a positive case is also counted as false acceptance if accepted with wrong value.",
        "production_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/cause_binding_eval_v013588259.json")
    p.add_argument("--output",default="results/independent_binding_eval_v013588258.json")
    args=p.parse_args()
    data=json.loads(Path(args.data).read_text(encoding="utf-8-sig"))
    report=evaluate(data["cases"])
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","cases","accepted","correct_accept","false_accept","false_accept_rate","coverage","selective_accuracy")},ensure_ascii=False))
    print("report:",out)
if __name__=="__main__":main()
