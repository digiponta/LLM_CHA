"""v0.4.28.32: retrospective pairwise generalization failure inspection."""
import argparse,hashlib,json,math
from pathlib import Path
from diagnose_qa_generalization_v042831 import summarize

def inspect(data):
    base=summarize(data)
    hold=[r for r in data["records"] if r["split"]=="INTERNAL_GROUP_HOLDOUT"]
    positive=[r for r in hold if r["weak_label"] is True]
    negative=[r for r in hold if r["weak_label"] is False]
    pairs=[]
    for p in positive:
        for n in negative:
            ps,ns=p["uncalibrated_score"],n["uncalibrated_score"]
            pairs.append({"positive_id":p["id"],"positive_turn":p["turn"],
                "negative_id":n["id"],"negative_turn":n["turn"],
                "positive_score":ps,"negative_score":ns,"margin":round(ps-ns,6),
                "ranking":"CORRECT" if ps>ns else "TIE" if ps==ns else "INVERTED"})
    correct=sum(p["ranking"]=="CORRECT" for p in pairs)
    tied=sum(p["ranking"]=="TIE" for p in pairs)
    inverted=sum(p["ranking"]=="INVERTED" for p in pairs)
    auc=round((correct+.5*tied)/len(pairs),6) if pairs else None
    if auc!=base["holdout_weak_label_ranking_auc"]:raise ValueError("AUC mismatch")
    pairs.sort(key=lambda p:(p["margin"],p["positive_id"],p["negative_id"]))
    return {"version":"v0.4.28.32","mode":"INTERNAL_HOLDOUT_RANKING_FAILURE_DIAGNOSTIC",
      "source_version":data["version"],"weak_label_source":"chatgpt",
      "human_ground_truth":False,"independent_external_holdout":False,
      "trained_or_calibrated":False,"runtime_modified":False,
      "train_class_distribution":base["splits"]["TRAIN"],
      "holdout_class_distribution":base["splits"]["INTERNAL_GROUP_HOLDOUT"],
      "holdout_positive":len(positive),"holdout_negative":len(negative),
      "positive_negative_pairs":len(pairs),"correct_pairs":correct,
      "tied_pairs":tied,"inverted_pairs":inverted,
      "ranking_auc":auc,
      "worst_inverted_pairs":[p for p in pairs if p["ranking"]=="INVERTED"][:12],
      "notes":"Pair scores share observations, so pair counts are not independent samples; ranking failures do not establish model root cause."}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    try:
        src,dst=Path(args.input),Path(args.output)
        if not src.is_file() or src.is_symlink() or dst.exists() or dst.is_symlink():
            raise ValueError("invalid input/output")
        result=inspect(json.loads(src.read_text(encoding="utf-8-sig")))
        result["source_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("holdout_positive","holdout_negative","positive_negative_pairs","correct_pairs","tied_pairs","inverted_pairs","ranking_auc")}))
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        parser.exit(1,f"ranking failure inspection failed: {e}\n")
if __name__=="__main__":main()
