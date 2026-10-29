#!/usr/bin/env python3
"""Diagnose retrieval separation using held-out AI-reviewed labels; no training."""
import argparse,csv,json,math,statistics
from collections import defaultdict
from pathlib import Path
from compare_holdout_retrieval_v0135874 import read_csv,evaluate

def summarize(values):
    if not values:return {"n":0}
    x=sorted(values);n=len(x)
    return {"n":n,"min":x[0],"mean":statistics.mean(x),"median":statistics.median(x),
            "max":x[-1],"p10":x[int((n-1)*.1)],"p90":x[int((n-1)*.9)]}

def diagnose(reviews,scores,top=5):
    report=evaluate(reviews,scores) # checks coverage/duplicate pairs
    reference={(r["query_id"],r["candidate_id"]):r["answer_reusable"].strip().lower()=="true" for r in reviews}
    questions={}
    for r in reviews:
        questions.setdefault(r["query_id"],r.get("query",""))
    per=defaultdict(list);pos=[];neg=[]
    for r in scores:
        key=(r["query_id"],r["candidate_id"])
        value=float(r["score"])
        (pos if reference[key] else neg).append(value)
        per[key[0]].append((key[1],value,reference[key]))
    cases=[]
    for q,values in sorted(per.items()):
        ranked=sorted(values,key=lambda x:(-x[1],x[0]))
        positives=[(i+1,c,s) for i,(c,s,ok) in enumerate(ranked) if ok]
        cases.append({"query_id":q,"query":questions[q],"first_positive_rank":positives[0][0] if positives else None,
          "best_positive_score":max((s for c,s,ok in values if ok),default=None),
          "best_negative_score":max((s for c,s,ok in values if not ok),default=None),
          "top_candidates":[{"candidate_id":c,"score":s,"reusable":ok} for c,s,ok in ranked[:top]]})
    eligible=[c for c in cases if c["best_positive_score"] is not None and c["best_negative_score"] is not None]
    margins=[c["best_positive_score"]-c["best_negative_score"] for c in eligible]
    return {"status":"PROVISIONAL_DIAGNOSTIC","evaluation":{k:v for k,v in report.items() if k!="per_query"},
       "positive_scores":summarize(pos),"negative_scores":summarize(neg),
       "per_query_margin":summarize(margins),
       "positive_beats_all_negative_queries":sum(m>0 for m in margins),
       "eligible_margin_queries":len(margins),"cases":cases,
       "caution":"AI-reviewed provisional labels; no independent human approval. No runtime acceptance gate is evaluated."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",required=True)
    p.add_argument("--ranking",required=True)
    p.add_argument("--output",default="results/semantic_retrieval_diagnostics_v0135876.json")
    p.add_argument("--top",type=int,default=5)
    a=p.parse_args()
    if a.top<1:p.error("--top must be >=1")
    result=diagnose(read_csv(a.review),read_csv(a.ranking),a.top)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="cases"},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
