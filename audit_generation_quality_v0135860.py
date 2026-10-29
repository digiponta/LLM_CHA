"""v0.13.58.60: Compare NLL against human-reviewed free generation.
No LLM-as-judge claims. Auto metrics are diagnostics, not semantic quality.
"""
import argparse,csv,json,collections,re
from pathlib import Path
FIELDS=("relevance","naturalness","factuality","repetition")
def auto_metrics(s):
    s=str(s)
    chunks=[s[i:i+4] for i in range(max(0,len(s)-3))]
    repeated=max(collections.Counter(chunks).values(),default=0)
    return {"chars":len(s),"replacement_characters":s.count("\ufffd"),
            "max_4gram_repetition":repeated,"empty":not bool(s.strip())}
def score(row):
    ratings={}
    for name in FIELDS:
        value=str(row.get(name,"")).strip()
        if not value:continue
        if value not in ("1","2","3","4","5"):
            raise ValueError(f"{row.get('id')}: invalid {name}={value!r}; use 1-5 or blank")
        ratings[name]=int(value)
    return ratings
def analyze(summary_path,review_path,output):
    if output.exists():raise FileExistsError(output)
    summary=json.loads(summary_path.read_text(encoding="utf-8-sig"))
    arms={(int(c["train_budget"]),int(c["updates"])):c for c in summary["conditions"]}
    with review_path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if not rows:raise ValueError("empty review")
    seen=set();group=collections.defaultdict(list)
    for row in rows:
        key=(int(row["train_budget"]),int(row["updates"]))
        if key not in arms:raise ValueError(f"unexpected experiment {key}")
        identity=(*key,row["id"])
        if identity in seen:raise ValueError(f"duplicate {identity}")
        seen.add(identity)
        item={**row,"auto":auto_metrics(row["generated"]),"human":score(row)}
        group[key].append(item)
    details=[]
    for key,arm in arms.items():
        items=group.get(key,[])
        if len(items)!=8:raise ValueError(f"expected 8 holdout answers in {key}, found {len(items)}")
        human={name:([i["human"][name] for i in items if name in i["human"]]) for name in FIELDS}
        all_rated=all(len(v)==len(items) for v in human.values())
        details.append({"train_budget":key[0],"updates":key[1],
            "validation_nll":arm["final_validation_nll"],
            "generation_count":len(items),
            "empty_outputs":sum(i["auto"]["empty"] for i in items),
            "replacement_character_outputs":sum(bool(i["auto"]["replacement_characters"]) for i in items),
            "repetition_4gram_gt_2":sum(i["auto"]["max_4gram_repetition"]>2 for i in items),
            "mean_chars":sum(i["auto"]["chars"] for i in items)/len(items),
            "human_review_complete":all_rated,
            "human_mean":{name:sum(v)/len(v) if v else None for name,v in human.items()},
            "human_rated_count":{name:len(v) for name,v in human.items()}})
    # With three runs on the same 8 prompts, difference in NLL is not evidence
    # for semantic-quality improvement until human ratings are supplied.
    output.mkdir(parents=True,exist_ok=False)
    result={"version":"v0.13.58.60","status":"HUMAN_REVIEW_COMPLETE" if all(x["human_review_complete"] for x in details) else "HUMAN_REVIEW_PENDING",
            "nll_and_quality":details,"rating_scale":"1=poor, 5=excellent for all fields (repetition: 5=no harmful repetition)",
            "claim_boundary":"Auto diagnostics are not semantic or factual quality ratings",
            "production_approved":False}
    (output/"quality_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--summary",type=Path,default=Path("results/replay25_sweep_v0135859_summary/summary.json"))
    p.add_argument("--review",type=Path,default=Path("results/replay25_sweep_v0135859_summary/review.csv"))
    p.add_argument("--output",type=Path,default=Path("results/generation_quality_v0135860"))
    a=p.parse_args();analyze(a.summary,a.review,a.output)
if __name__=="__main__":main()
