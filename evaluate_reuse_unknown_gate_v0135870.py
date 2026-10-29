"""v0.13.58.70: integrated Answer Reuse Reranker + Unknown Gate.

Development-set comparison only. Scores are not calibrated probabilities.
The original Ruri score is retained as the acceptance threshold; the margin is
computed *after* reranking. Prevents boosted lexical signals from masquerading
as absolute semantic confidence.
"""
import argparse,json
from pathlib import Path
from rerank_answer_reuse_v0135869 import read_reviews,rank_candidates

def choose(items,method,threshold,margin):
    original=sorted(items,key=lambda r:int(r["rank"]))
    ranked=(original if method=="baseline" else rank_candidates(original[0]["query"],original))
    first=ranked[0]
    second=ranked[1] if len(ranked)>1 else None
    first_score=float(first["base_score"])
    margin_key="adjusted_score" if method=="baseline" else "reuse_score"
    gap=float(first[margin_key])-float(second[margin_key]) if second else float("inf")
    accepted=first_score>=threshold and gap>=margin
    return {"accepted":accepted,"candidate_id":first["candidate_id"],
            "answer":first["candidate_answer"] if accepted else None,
            "base_score":first_score,"gap":gap,
            "top1_reusable_for_evaluation":first["answer_reusable"]=="YES",
            "reason":"ACCEPT" if accepted else ("LOW_BASE_SCORE" if first_score<threshold else "LOW_MARGIN")}

def evaluate(groups,method,threshold,margin):
    rows=[]
    for q,items in groups.items():
        d=choose(items,method,threshold,margin)
        any_good=any(x["answer_reusable"]=="YES" for x in items)
        rows.append({"query_id":q,"has_reusable_in_top10":any_good,**d})
    accepted=[x for x in rows if x["accepted"]]
    viable=[x for x in rows if x["has_reusable_in_top10"]]
    not_viable=[x for x in rows if not x["has_reusable_in_top10"]]
    safe=sum(x["top1_reusable_for_evaluation"] for x in accepted)
    def div(a,b):return a/b if b else None
    return {"method":method,"threshold":threshold,"margin":margin,"accepted":len(accepted),
      "coverage":div(len(accepted),len(rows)),"accepted_answer_accuracy":div(safe,len(accepted)),
      "false_accept_count":len(accepted)-safe,
      "top10_viable_count":len(viable),"top10_nonviable_count":len(not_viable),
      "viable_query_accepted":sum(x["accepted"] for x in viable),
      "viable_query_correctly_answered":sum(x["accepted"] and x["top1_reusable_for_evaluation"] for x in viable),
      "nonviable_reject_rate":div(sum(not x["accepted"] for x in not_viable),len(not_viable)),
      "rows":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",type=Path,default=Path("data/answer_reuse_review_v0135867.csv"))
    p.add_argument("--output",type=Path,default=Path("results/reuse_unknown_gate_v0135870.json"))
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    groups=read_reviews(a.review)
    arms=[evaluate(groups,method,t,m)
          for method in ("baseline","reuse_reranked")
          for t in (0.85,0.88,0.90,0.92,0.94)
          for m in (0,0.005,0.01,0.02)]
    report={"version":"v0.13.58.70","development_only":True,
      "independent_holdout":False,"score_calibrated":False,
      "gate_note":"Base semantic score of selected candidate >= threshold; final ranking margin >= margin.",
      "unknown_scope":"top10 only; no proven absence from 56 training answers",
      "arms":arms}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for x in arms:
        print(json.dumps({k:v for k,v in x.items() if k!="rows"},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
