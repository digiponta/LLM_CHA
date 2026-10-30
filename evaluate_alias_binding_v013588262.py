"""Evaluate alias-aware binding on the frozen real-source diagnostic set.

This is not a reviewed independent holdout and never changes human review fields.
"""
import argparse,json
from pathlib import Path
from evidence_alias_binding_v013588262 import answer_or_abstain
from evaluate_cause_binding_v013588259 import evaluate as evaluate_synthetic
import evaluate_cause_binding_v013588259 as synthetic_module

def evaluate_real(data):
    cases=[]
    for row in data.get("cases",[]):
        r=answer_or_abstain(row["question"],row["evidence"])
        cases.append({"id":row["id"],"question":row["question"],
                      "source_title":row["source"]["title"],"status":r["status"],
                      "sentence":r.get("sentence"),"value":r.get("value"),
                      "surface_value":r.get("surface_value"),
                      "review_status":row["review"]["status"]})
    return {"status":"REAL_EVIDENCE_DIAGNOSTIC_ONLY","case_count":len(cases),
            "accepted":sum(x["status"]=="BOUND_EXTRACT_ACCEPTED" for x in cases),
            "cases":cases,"holdout_approved":False,"production_changed":False,
            "caution":"No gold labels: accepted counts are NOT precision or accuracy."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--real-data",default="data/wiki_evidence_review_v013588260.json")
    p.add_argument("--synthetic-data",default="data/independent_binding_eval_v013588258.json")
    p.add_argument("--output",default="results/alias_binding_v013588262.json")
    args=p.parse_args()
    real=json.loads(Path(args.real_data).read_text(encoding="utf-8-sig"))
    synthetic=json.loads(Path(args.synthetic_data).read_text(encoding="utf-8-sig"))
    real_report=evaluate_real(real)
    original=synthetic_module.answer_or_abstain
    try:
        synthetic_module.answer_or_abstain=answer_or_abstain
        synthetic_report=evaluate_synthetic(synthetic["cases"])
    finally:
        synthetic_module.answer_or_abstain=original
    # Legacy synthetic metrics remain a separate preservation baseline.
    report={"status":"ALIAS_BINDING_OFFLINE_DIAGNOSTIC",
            "real":real_report,"alias_synthetic_metrics":{k:synthetic_report.get(k) for k in
              ("cases","accepted","correct_accept","false_accept","false_accept_rate","coverage","selective_accuracy")},
            "production_changed":False}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],
                      "real_cases":real_report["case_count"],"real_extracted":real_report["accepted"],
                      "synthetic_correct":synthetic_report["correct_accept"],
                      "synthetic_false_accept":synthetic_report["false_accept"],"report":str(path)},ensure_ascii=False))
if __name__=="__main__":main()
