"""Read-only Semantic Memory compatibility diagnostics, not semantic entailment.

No same-subject definition is labeled contradictory merely for differing wording.
"""
import argparse
import json
import unicodedata
from pathlib import Path
from semantic_proposition_v1090 import load_propositions

def normalized(s):
    return unicodedata.normalize("NFKC",str(s or "")).strip(" 。、\t\n")

def compare(candidate,existing):
    subject=normalized(candidate.get("subject"))
    meaning=normalized(candidate.get("meaning"))
    if not subject or not meaning or candidate.get("quality_gate")!="PASS":
        return {"status":"BLOCKED_UNQUALIFIED","matches":[]}
    rows=[x for x in existing if normalized(x.get("subject"))==subject]
    if not rows:return {"status":"NO_MATCHING_SUBJECT","matches":[]}
    exact=[x for x in rows if normalized(x.get("value"))==meaning]
    if exact:return {"status":"EXACT_VALUE_MATCH","matches":exact}
    partial=[x for x in rows if normalized(x.get("value")) in meaning or meaning in normalized(x.get("value"))]
    if partial:return {"status":"POSSIBLE_ELABORATION","matches":partial}
    return {"status":"REVIEW_SENSE_OR_CONFLICT","matches":rows}

def inspect(candidates,existing):
    rows=[]
    for candidate in candidates:
        finding=compare(candidate,existing)
        rows.append({"candidate_id":candidate.get("id"),"subject":candidate.get("subject"),
                     "meaning":candidate.get("meaning"),"compatibility":finding["status"],
                     "existing":finding["matches"],"manual_review_required":True,
                     "approved":False,"production_promoted":False})
    return {"status":"SEMANTIC_COMPATIBILITY_DIAGNOSTIC","case_count":len(rows),
            "rows":rows,"approved_count":0,"production_changed":False,
            "caution":"Lexical similarity only; neither contradiction nor entailment is established."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",default="results/sense_definition_quality_v013588270.json")
    p.add_argument("--propositions",default="data/semantic_propositions_v1090.jsonl")
    p.add_argument("--output",default="results/sense_compatibility_v013588271.json")
    a=p.parse_args()
    data=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))
    path=Path(a.propositions)
    records=[{"subject":x.subject,"value":x.value} for x in load_propositions(path)]
    result=inspect(data.get("candidates",[]),records)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={}
    for row in result["rows"]:
        key=row["compatibility"]
        summary[key]=summary.get(key,0)+1
    print(json.dumps({"status":result["status"],"cases":result["case_count"],
                      "counts":summary,"approved":0,"report":str(out)},ensure_ascii=False))
if __name__=="__main__":main()
