"""Compare v0.4.14 exploratory boundary labels against frozen v0.4.13 labels."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from evaluate_proposition_holdout_v0413 import FIXTURE,evidence
from definition_property_boundary_v0414 import classify,DEFINITION
from external_candidate_store_v0407 import _atomic_write

def evaluate(path=FIXTURE):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version")!="v0.4.13" or data.get("independent_blind") is not False:
        raise ValueError("invalid frozen evaluation input")
    cases=data["cases"]
    tp=fp=fn=tn=0;details=[]
    for c in cases:
        r=classify(evidence(c))
        predicted=any(x["classification"]==DEFINITION for x in r["items"])
        expected=c["expected_extract"]
        for x in r["items"]:
            if c["text"][x["evidence_start"]:x["evidence_end"]]!=x["literal"]:
                raise ValueError("invalid literal span")
        tp+=int(expected and predicted)
        fp+=int(not expected and predicted)
        fn+=int(expected and not predicted)
        tn+=int(not expected and not predicted)
        details.append({"id":c["id"],"expected":expected,"predicted":predicted,
                        "match":expected==predicted,
                        "classifications":[x["classification"] for x in r["items"]]})
    return {"version":"v0.4.14",
            "protocol":"RETROSPECTIVE_BOUNDARY_ANALYSIS_NOT_NEW_HOLDOUT",
            "total":len(cases),"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn) if tp+fn else None,
            "details":details,"truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report")
    args=p.parse_args()
    d=evaluate()
    if args.report:_atomic_write(args.report,d)
    print(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
