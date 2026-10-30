"""Diagnostic-only evaluation, with unchanged source review state."""
import argparse,json
from pathlib import Path
from evidence_dynamic_definition_v013588263 import answer_or_abstain
from evaluate_cause_binding_v013588259 import evaluate as synthetic_evaluate
import evaluate_cause_binding_v013588259 as synthetic_module

def evaluate(real,synthetic):
    rows=[]
    for item in real["cases"]:
        result=answer_or_abstain(item["question"],item["evidence"])
        rows.append({"id":item["id"],"question":item["question"],
                     "status":result["status"],"method":result.get("method"),
                     "sentence":result.get("sentence"),
                     "value":result.get("value"),"review_status":item["review"]["status"]})
    saved=synthetic_module.answer_or_abstain
    try:
        synthetic_module.answer_or_abstain=answer_or_abstain
        baseline=synthetic_evaluate(synthetic["cases"])
    finally:
        synthetic_module.answer_or_abstain=saved
    return {"status":"DYNAMIC_DEFINITION_OFFLINE_DIAGNOSTIC",
            "real":{"case_count":len(rows),"extracted":sum(x["status"]=="BOUND_EXTRACT_ACCEPTED" for x in rows),
                    "cases":rows,"holdout_approved":False},
            "synthetic":{k:baseline[k] for k in ("cases","accepted","correct_accept","false_accept","false_accept_rate","selective_accuracy")},
            "production_changed":False,
            "caution":"Wikipedia records are unreviewed and truncated. Extracted count is not accuracy. Synthetic cases are development fixtures."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--real-data",default="data/wiki_evidence_review_v013588260.json")
    p.add_argument("--synthetic-data",default="data/independent_binding_eval_v013588258.json")
    p.add_argument("--output",default="results/dynamic_definition_v013588263.json")
    a=p.parse_args()
    real=json.loads(Path(a.real_data).read_text(encoding="utf-8-sig"))
    synthetic=json.loads(Path(a.synthetic_data).read_text(encoding="utf-8-sig"))
    report=evaluate(real,synthetic)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"real_extracted":report["real"]["extracted"],
          "real_total":report["real"]["case_count"],"synthetic_correct":report["synthetic"]["correct_accept"],
          "synthetic_false_accept":report["synthetic"]["false_accept"],"report":str(dest)},ensure_ascii=False))
if __name__=="__main__":main()
