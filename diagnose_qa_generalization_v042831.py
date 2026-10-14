"""v0.4.28.31: observational score diagnostics on frozen v0.4.28.30 output.

NO threshold fitting, independent-test claims, or runtime decisions.
"""
import argparse, hashlib, json, math, statistics
from pathlib import Path

SPLITS=("TRAIN","INTERNAL_GROUP_HOLDOUT")
def summarize(data):
    if data.get("version")!="v0.4.28.30" or data.get("mode")!="INTERNAL_GROUPED_DEVELOPMENT_EVALUATION":
        raise ValueError("expected v0.4.28.30 grouped development report")
    records=data.get("records")
    if not isinstance(records,list) or len(records)!=data.get("train_labeled",0)+data.get("holdout_labeled",0):
        raise ValueError("invalid record count")
    seen=set();by_split={s:{True:[],False:[]} for s in SPLITS}
    for row in records:
        key=(row.get("id"),row.get("turn"))
        if key in seen:raise ValueError("duplicate record")
        seen.add(key)
        split=row.get("split");label=row.get("weak_label");score=row.get("uncalibrated_score")
        if split not in by_split or type(label) is not bool or type(score) not in (int,float):
            raise ValueError("invalid record")
        if not math.isfinite(score) or not 0<=score<=1:raise ValueError("invalid score")
        by_split[split][label].append(float(score))
    if sum(len(x) for x in by_split["TRAIN"].values())!=data["train_labeled"]:
        raise ValueError("train mismatch")
    if sum(len(x) for x in by_split["INTERNAL_GROUP_HOLDOUT"].values())!=data["holdout_labeled"]:
        raise ValueError("holdout mismatch")
    def desc(xs):
        if not xs:return {"count":0,"mean":None,"min":None,"max":None}
        return {"count":len(xs),"mean":round(statistics.mean(xs),6),
          "min":round(min(xs),6),"max":round(max(xs),6)}
    summaries={s:{"positive":desc(by_split[s][True]),"negative":desc(by_split[s][False])} for s in SPLITS}
    # Ranking probability only if both provisional classes appear; no calibrated classification.
    hold=by_split["INTERNAL_GROUP_HOLDOUT"]
    pairs=[(p,n) for p in hold[True] for n in hold[False]]
    auc=(sum(1 if p>n else .5 if p==n else 0 for p,n in pairs)/len(pairs)) if pairs else None
    return {"version":"v0.4.28.31","mode":"OFFLINE_UNCALIBRATED_SCORE_DIAGNOSTIC",
      "development_only":True,"human_ground_truth":False,"external_holdout":False,
      "no_threshold_optimization":True,"runtime_modified":False,
      "original_checkpoint_verified":data.get("checkpoint_verified") is True,
      "splits":summaries,"holdout_positive_negative_pairs":len(pairs),
      "holdout_weak_label_ranking_auc":round(auc,6) if auc is not None else None,
      "auc_is_provisional_internal_diagnostic":True,
      "notes":"Scores are in-sample TRAIN or internal grouped development holdout, using ChatGPT weak labels. No independent generalization claim."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        inp,out=Path(a.input),Path(a.output)
        if not inp.is_file() or inp.is_symlink() or out.exists() or out.is_symlink():
            raise ValueError("invalid input or existing output")
        result=summarize(json.loads(inp.read_text(encoding="utf-8-sig")))
        result["source_sha256"]=hashlib.sha256(inp.read_bytes()).hexdigest()
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"train":sum(result["splits"]["TRAIN"][c]["count"] for c in ("positive","negative")),
          "holdout":sum(result["splits"]["INTERNAL_GROUP_HOLDOUT"][c]["count"] for c in ("positive","negative")),
          "holdout_ranking_auc":result["holdout_weak_label_ranking_auc"]}))
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:p.exit(1,f"score diagnostic failed: {e}\n")
if __name__=="__main__":main()
