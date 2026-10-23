"""v0.7.16: read-only four-fact paraphrase failure diagnosis.

Consumes the existing v0.7.15 report (no model training, no mutation of
Approved or Candidate stores). This reports lexical exact match, cross-fact
symbol leakage, and empty/other failures. Exact answers must not be confused
with semantic or factual correctness.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from prepare_multi_knowledge_v079 import FACTS

def diagnose(report):
    cases=report["holdout_cases"]
    symbols={answer:question for question,answer,_ in FACTS}
    per_fact={answer:{"count":0,"exact":0,"wrong_fact":0,"contains_correct":0,"other":0}
              for answer in symbols}
    details=[]
    for row in cases:
        expected=row["reference"]
        if expected not in symbols:raise ValueError("unexpected reference")
        generated=row["outputs"]["experimental"]
        exact=(generated.strip()==expected)
        correct_in_output=expected in generated
        wrong_codes=[code for code in symbols if code!=expected and code in generated]
        kind=("exact" if exact else "cross_fact_confusion" if wrong_codes
              else "contains_reference_but_not_exact" if correct_in_output
              else "empty" if not generated.strip() else "other")
        per_fact[expected]["count"]+=1
        per_fact[expected]["exact"]+=int(exact)
        per_fact[expected]["wrong_fact"]+=int(bool(wrong_codes))
        per_fact[expected]["contains_correct"]+=int(correct_in_output and not exact)
        per_fact[expected]["other"]+=int(kind in ("other","empty"))
        details.append({"question":row["question"],"reference":expected,
                        "generated":generated,"class":kind,
                        "wrong_fact_codes":wrong_codes})
    counts=dict(Counter(item["class"] for item in details))
    return {"version":"v0.7.16","source_version":report.get("version"),
            "cases":len(details),"class_counts":counts,"by_fact":per_fact,
            "details":details,"note":"Exact-string and cross-fact-code analysis only; no factual validation."}

def run(report_path,output_path):
    src=Path(report_path).resolve()
    dest=Path(output_path).resolve()
    if src==dest:raise ValueError("output would overwrite input")
    report=json.loads(src.read_text(encoding="utf-8"))
    if report.get("version")!="v0.7.15" or not isinstance(report.get("holdout_cases"),list):
        raise ValueError("not a v0.7.15 report")
    result=diagnose(report)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",default="results/multi_fact_v0715/summary_v0715.json")
    p.add_argument("--output",default="results/multi_fact_v0716/diagnosis.json")
    a=p.parse_args()
    result=run(a.report,a.output)
    print(json.dumps({"version":result["version"],"cases":result["cases"],
                      "class_counts":result["class_counts"],"by_fact":result["by_fact"],
                      "output":a.output},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
