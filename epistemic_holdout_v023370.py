"""v0.2.33.70: conservative opinion restoration + separate holdout protocol.

This is an offline classifier experiment; never writes to semantic memory, truth
state, model weights or the existing gold-label worksheet.
"""
import argparse,hashlib,json,re
from pathlib import Path
from epistemic_calibration_v023368 import classify_v68,LABELS
from epistemic_review_analysis_v023369 import error_analysis

def classify_v70(sentence):
    labels=classify_v68(sentence)
    # Repair the known v68 false-negative on explicit perspective constructions.
    if re.search(r"(?:的に)?考えると|(?:現象論的|哲学的|解釈的)な(?:観点|見方)",sentence):
        if labels==["CONTEXT_ONLY"]:labels=[]
        if "OPINION" not in labels:labels.append("OPINION")
    # v68 avoids interpreting technical "可能性" alone as a hypothesis;
    # "的には" alone is ambiguous and deliberately not automatically OPINION.
    return labels or ["CONTEXT_ONLY"]

def holdout_fixture():
    # Independently authored review examples; not copies of 8 Nagato occurrences.
    # Gold labels are PROPOSED fixture labels, not independently human-adjudicated.
    return [
        ("私の解釈では、この現象は別の説明も可能だ。",["CONTEXT_ONLY"]),
        ("このモデルは仮説にすぎない。",["HYPOTHESIS"]),
        ("この現象は時計の針のようなもの。",["ANALOGY"]),
        ("これは現象論的な見方である。",["OPINION"]),
        ("観測可能性と可能性の分布を定義する。",["CONTEXT_ONLY"]),
        ("別の観点では、世界は舞台のようなものだ。",["ANALOGY","OPINION"]),
        ("統計的には結果が確率で定まる。",["CONTEXT_ONLY"]),
        ("宇宙の進化を仮説として考えると、別の説明があるかもしれない。",["HYPOTHESIS","OPINION"]),
    ]

def build_holdout():
    from corpus_context_classification_v023367 import classify
    rows=[]
    for i,(sentence,proposed) in enumerate(holdout_fixture()):
        rows.append({"sample_id":f"H{i+1:02d}","context":sentence,
                    "context_sha256":hashlib.sha256(sentence.encode("utf8")).hexdigest(),
                    "baseline_labels":classify(sentence),
                    "candidate_labels":classify_v68(sentence),
                    "v70_labels":classify_v70(sentence),
                    "proposed_gold_labels":proposed,
                    "gold_labels":None,"review_status":"UNREVIEWED"})
    return {"version":"v0.2.33.70","origin":"separate-authored-fixtures",
            "note":"Independently authored *inputs*, NOT independent adjudication. Human review required.",
            "rows":rows}

def validate_and_score(data):
    rows=data.get("rows")
    if not isinstance(rows,list) or not rows:raise ValueError("empty_holdout")
    valid_status={"REVIEWED","UNREVIEWED"}
    for r in rows:
        if r.get("review_status") not in valid_status:raise ValueError("bad_status")
        if hashlib.sha256(r.get("context","").encode("utf8")).hexdigest()!=r.get("context_sha256"):
            raise ValueError("context_changed")
        if r.get("baseline_labels")!=__import__("corpus_context_classification_v023367",fromlist=["classify"]).classify(r["context"]):
            raise ValueError("baseline_modified")
        if r.get("candidate_labels")!=classify_v68(r["context"]) or r.get("v70_labels")!=classify_v70(r["context"]):
            raise ValueError("predictions_modified")
        if r["review_status"]=="UNREVIEWED" and r.get("gold_labels") is not None:
            raise ValueError("unreviewed_gold_present")
        if r["review_status"]=="REVIEWED":
            labels=r.get("gold_labels")
            if not isinstance(labels,list) or not labels or any(x not in LABELS for x in labels):
                raise ValueError("bad_gold")
    reviewed=[r for r in rows if r["review_status"]=="REVIEWED"]
    if not reviewed:return {"reviewed_count":0,"total_count":len(rows),"metrics":None}
    comparison={}
    for pred in ("baseline_labels","candidate_labels","v70_labels"):
        renamed=[{"review_status":"REVIEWED","gold_labels":r["gold_labels"],
                  "baseline_labels":r[pred],"candidate_labels":r[pred],"mention_start":i,
                  "context":r["context"]} for i,r in enumerate(reviewed)]
        comparison[pred]=error_analysis(renamed)["metrics"]["baseline"]
    return {"reviewed_count":len(reviewed),"total_count":len(rows),"metrics":comparison}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="results/epistemic_holdout_v023370.json")
    parser.add_argument("--score",help="Score a separately human-reviewed holdout JSON")
    args=parser.parse_args()
    if args.score:
        print(json.dumps(validate_and_score(json.loads(Path(args.score).read_text(encoding="utf8"))),
                         ensure_ascii=False,indent=2))
    else:
        path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x",encoding="utf8") as f:json.dump(build_holdout(),f,ensure_ascii=False,indent=2)
        print(f"Prepared {len(holdout_fixture())} separate holdout examples; review_status=UNREVIEWED; no scores.")
        print(path)

if __name__=="__main__":main()
