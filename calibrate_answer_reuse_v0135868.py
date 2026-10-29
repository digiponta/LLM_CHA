"""v0.13.58.68: gate calibration on human-reviewed answer reuse records.

This is development-only calibration on previously inspected examples.
Only a fully reviewed top-10 is admissible; UNKNOWN is never asserted
for all 56 unless all 56 answers have been examined.
"""
import argparse,csv,json
from pathlib import Path
from collections import defaultdict

def load_review(path):
    with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if not rows:raise ValueError("empty review")
    groups=defaultdict(list)
    for r in rows:
        q=r["query_id"]
        if r["review_status"]!="APPROVED" or r["answer_reusable"] not in ("YES","NO"):
            raise ValueError(f"{q}: incomplete approval")
        groups[q].append(r)
    for q,items in groups.items():
        if len(items)!=10 or len({x["candidate_id"] for x in items})!=10:
            raise ValueError(f"{q}: require 10 uniquely reviewed candidates")
        ranks=sorted(int(x["rank"]) for x in items)
        if ranks!=list(range(1,11)):raise ValueError(f"{q}: invalid ranks")
    return groups

def evaluate(groups,threshold,margin):
    results=[]
    for q,items in groups.items():
        ordered=sorted(items,key=lambda x:int(x["rank"]))
        top=ordered[0];second=ordered[1]
        score=float(top["base_score"])
        gap=float(top["adjusted_score"])-float(second["adjusted_score"])
        accepted=score>=threshold and gap>=margin
        top_correct=top["answer_reusable"]=="YES"
        any_good=any(x["answer_reusable"]=="YES" for x in ordered)
        results.append({"query_id":q,"score":score,"margin":gap,"accepted":accepted,
                        "top1_reusable":top_correct,"top10_any_reusable":any_good,
                        "top_hit":top["candidate_id"]})
    accepted=[r for r in results if r["accepted"]]
    known=[r for r in results if r["top10_any_reusable"]]
    no_top10=[r for r in results if not r["top10_any_reusable"]]
    def frac(a,b):return a/b if b else None
    return {"threshold":threshold,"margin":margin,"total_queries":len(results),
            "accepted_count":len(accepted),"coverage":frac(len(accepted),len(results)),
            "accepted_answer_accuracy":frac(sum(r["top1_reusable"] for r in accepted),len(accepted)),
            "false_accept_count":sum(not r["top1_reusable"] for r in accepted),
            "known_top10_coverage":frac(sum(r["accepted"] for r in known),len(known)),
            "no_reusable_top10_reject_rate":frac(sum(not r["accepted"] for r in no_top10),len(no_top10)),
            "known_top10_count":len(known),"no_reusable_top10_count":len(no_top10),
            "per_question":results}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",type=Path,default=Path("data/answer_reuse_review_v0135867.csv"))
    p.add_argument("--output",type=Path,default=Path("results/answer_reuse_calibration_v0135868.json"))
    a=p.parse_args()
    groups=load_review(a.review)
    # Intentionally a predeclared sweep: do not choose a winning threshold on
    # this data and call it independent performance.
    thresholds=[0.85,0.88,0.90,0.92,0.94,0.96]
    margins=[0,0.005,0.01,0.02,0.04]
    arms=[evaluate(groups,t,m) for t in thresholds for m in margins]
    report={"version":"v0.13.58.68","evaluation":"REUSED_DEVELOPMENT_ONLY",
      "independent_test":False,"calibrated_probability":False,
      "unknown_ground_truth_scope":"NO_REUSABLE_IN_REVIEWED_TOP10_ONLY",
      "warning":"Accuracy is on previously observed examples; no deployment threshold is validated.",
      "arms":arms}
    if a.output.exists():raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in arms:
        print(json.dumps({k:v for k,v in r.items() if k!="per_question"},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
