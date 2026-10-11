"""v0.2.33.69 — independently reviewed, source-checked epistemic error analysis.

This script NEVER writes gold labels, facts, semantic memory, truth state or weights.
The reviewer must explicitly assign gold labels in a separate copy of the worksheet.
"""
import argparse,hashlib,json
from pathlib import Path
from epistemic_calibration_v023368 import LABELS,evaluate_reviewed
from corpus_context_classification_v023367 import mentions

PREDICTIONS=("baseline_labels","candidate_labels")

def validate_review(data,source):
    if not isinstance(data,dict) or not isinstance(data.get("rows"),list):
        raise ValueError("invalid_worksheet")
    source=Path(source)
    canonical=mentions(source,data.get("concept",""))
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    if sha!=data.get("source_sha256") or len(canonical)!=len(data["rows"]):
        raise ValueError("source_or_row_count_mismatch")
    for n,(original,row) in enumerate(zip(canonical,data["rows"])):
        if (row.get("mention_start")!=original["mention_start"] or
            row.get("context")!=original["context"] or
            row.get("context_sha256")!=original["context_sha256"]):
            raise ValueError(f"source_context_mismatch:{n}")
        if row.get("review_status") not in ("REVIEWED","UNREVIEWED"):
            raise ValueError(f"invalid_review_status:{n}")
        labels=row.get("gold_labels")
        if row["review_status"]=="REVIEWED":
            if (not isinstance(labels,list) or not labels or
                len(labels)!=len(set(labels)) or any(x not in LABELS for x in labels)):
                raise ValueError(f"invalid_gold_labels:{n}")
        elif labels is not None:
            raise ValueError(f"unreviewed_gold_not_null:{n}")
        for key in PREDICTIONS:
            if not isinstance(row.get(key),list) or any(x not in LABELS for x in row[key]):
                raise ValueError(f"invalid_prediction:{n}")
    return data["rows"]

def error_analysis(rows):
    overall=evaluate_reviewed(rows)
    reviewed=[r for r in rows if r["review_status"]=="REVIEWED"]
    if not reviewed:
        return {"reviewed_count":0,"total_count":len(rows),"metrics":None,
                "by_label":None,"disagreements":[]}
    by_label={}
    for label in sorted(LABELS):
        scores={}
        for key in PREDICTIONS:
            tp=sum(label in r[key] and label in r["gold_labels"] for r in reviewed)
            fp=sum(label in r[key] and label not in r["gold_labels"] for r in reviewed)
            fn=sum(label not in r[key] and label in r["gold_labels"] for r in reviewed)
            p=tp/(tp+fp) if tp+fp else 0.0
            recall=tp/(tp+fn) if tp+fn else 0.0
            scores[key]={"tp":tp,"fp":fp,"fn":fn,"precision":p,"recall":recall,
                         "f1":2*p*recall/(p+recall) if p+recall else 0.0,
                         "support":tp+fn}
        by_label[label]=scores
    errors=[]
    for r in reviewed:
        gold=set(r["gold_labels"])
        if any(set(r[k])!=gold for k in PREDICTIONS):
            errors.append({"mention_start":r["mention_start"],
                           "context":r["context"],"gold_labels":r["gold_labels"],
                           "baseline_labels":r["baseline_labels"],
                           "candidate_labels":r["candidate_labels"],
                           "baseline_fp":sorted(set(r["baseline_labels"])-gold),
                           "baseline_fn":sorted(gold-set(r["baseline_labels"])),
                           "candidate_fp":sorted(set(r["candidate_labels"])-gold),
                           "candidate_fn":sorted(gold-set(r["candidate_labels"]))})
    return {"reviewed_count":len(reviewed),"total_count":len(rows),
            "metrics":overall["metrics"],"by_label":by_label,"disagreements":errors}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",required=True,help="User-reviewed copy of v68 worksheet JSON")
    p.add_argument("--source",default="data/data-nagato.txt")
    p.add_argument("--output",help="Optional new JSON analysis path (never overwritten)")
    args=p.parse_args()
    data=json.loads(Path(args.review).read_text(encoding="utf-8"))
    rows=validate_review(data,args.source)
    report=error_analysis(rows)
    if args.output:
        target=Path(args.output)
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
        print(target)
    else:
        print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
