"""v0.4.28.19: read-only QA relevance calibration inventory.

Human labels are never manufactured. Focused cases are review priorities only.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from review_semantic_relevance_v042813 import FIELDS,summarize
from evaluate_qa_lexical_shadow_v042818 import bigrams

FOCUS={"A04","A05","C05","C07"}

def inventory(validation, review_rows):
    human=summarize(validation,review_rows)
    labels={(r["id"],int(r["turn"])):r["labels"].get("final_relevant") for r in human["manual_evaluations"]}
    rows=[];seen=set()
    for record in validation["records"]:
        key=(record["id"],record["turn"])
        if key in seen:raise ValueError("duplicate input")
        seen.add(key)
        label=labels.get(key)
        q=record["question"];a=record.get("final_answer")
        qs=bigrams(q);ans=bigrams(a) if isinstance(a,str) else set()
        lexical=round(len(qs&ans)/len(qs),6) if qs and ans else None
        rows.append({"id":key[0],"turn":key[1],"question":q,"final_answer":a,
          "human_final_relevant":label,"lexical_overlap":lexical,
          "gate_resolution":record.get("gate_resolution"),
          "review_priority":"FOCUS_UNLABELED" if key[0] in FOCUS and label is None else
             "GENERAL_UNLABELED" if label is None else "LABELED",
          "calibration_partition":"DEVELOPMENT_ONLY"})
    if len(rows)!=64:raise ValueError("expected 64 turns")
    positives=sum(x["human_final_relevant"] is True for x in rows)
    negatives=sum(x["human_final_relevant"] is False for x in rows)
    rows.sort(key=lambda x:({"FOCUS_UNLABELED":0,"GENERAL_UNLABELED":1,"LABELED":2}[x["review_priority"]],str(x["id"]),x["turn"]))
    return {"version":"v0.4.28.19","mode":"REVIEW_DATA_INVENTORY",
      "development_only":True,"independent_holdout":False,
      "automatic_labels_added":0,"total_turns":64,
      "positive_labeled":positives,"negative_labeled":negatives,
      "unlabeled":64-positives-negatives,
      "balanced_binary_calibration_ready":positives>0 and negatives>0,
      "threshold_estimated":False,"records":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--reviews",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        paths=[Path(a.validation),Path(a.reviews)]
        dst=Path(a.output)
        if any(not x.is_file() or x.is_symlink() for x in paths):raise ValueError("invalid input")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        validation=json.loads(paths[0].read_text(encoding="utf-8"))
        with paths[1].open("r",encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=FIELDS:raise ValueError("invalid headers")
            reviews=list(reader)
        report=inventory(validation,reviews)
        report["sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:report[k] for k in ("total_turns","positive_labeled","negative_labeled","unlabeled","balanced_binary_calibration_ready")}))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as e:p.exit(1,f"inventory failed: {e}\n")
if __name__=="__main__":main()
