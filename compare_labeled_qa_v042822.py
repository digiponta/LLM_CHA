"""v0.4.28.22: descriptive comparison of explicitly reviewed QA answers only."""
import argparse,csv,json,statistics
from pathlib import Path
from prepare_qa_calibration_v042819 import inventory
from review_semantic_relevance_v042813 import FIELDS

def compare(validation,reviews):
    base=inventory(validation,reviews)
    groups={name:[r["lexical_overlap"] for r in base["records"]
            if r["human_final_relevant"] is expected and r["lexical_overlap"] is not None]
            for name,expected in (("positive",True),("negative",False))}
    stats={name:({"n":len(vals),"mean":round(statistics.mean(vals),6),
                   "median":round(statistics.median(vals),6),"min":min(vals),"max":max(vals)}
                 if vals else {"n":0,"mean":None,"median":None,"min":None,"max":None})
           for name,vals in groups.items()}
    ready=bool(groups["positive"] and groups["negative"])
    return {"version":"v0.4.28.22","mode":"DESCRIPTIVE_DEVELOPMENT_ONLY",
      "total_turns":64,"positive_labeled":base["positive_labeled"],
      "negative_labeled":base["negative_labeled"],"unlabeled":base["unlabeled"],
      "lexical_statistics":stats,
      "between_class_comparison_available":ready,
      "difference_in_means":round(stats["positive"]["mean"]-stats["negative"]["mean"],6) if ready else None,
      "semantic_agreement_statistics":"NOT_AVAILABLE_IN_THIS_INPUT",
      "classifier_accuracy":"NOT_MEASURED","threshold_estimated":False,
      "independent_holdout":False,"runtime_modified":False,
      "note":"Descriptive lexical overlap only; no semantic classifier or threshold."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--reviews",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        inp,review,out=Path(a.validation),Path(a.reviews),Path(a.output)
        if not inp.is_file() or inp.is_symlink() or not review.is_file() or review.is_symlink():raise ValueError("invalid input")
        if out.exists() or out.is_symlink():raise ValueError("output exists")
        val=json.loads(inp.read_text(encoding="utf-8"))
        with review.open(encoding="utf-8-sig",newline="") as f:
            rd=csv.DictReader(f)
            if rd.fieldnames!=FIELDS:raise ValueError("invalid CSV header")
            rows=list(rd)
        result=compare(val,rows)
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("positive_labeled","negative_labeled","unlabeled","between_class_comparison_available")}))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as e:
        p.exit(1,f"comparison failed: {e}\n")
if __name__=="__main__":main()
