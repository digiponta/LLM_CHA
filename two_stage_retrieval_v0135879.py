#!/usr/bin/env python3
"""Experimental two-stage retrieval + abstention metrics, v0.13.58.79.
No training or interaction with the dialogue runtime.
"""
import argparse, json
from pathlib import Path
from collections import defaultdict
from hybrid_retrieval_v0135878 import lexical_scores,minmax_by_query
from score_holdout_llm_sem_v0135875 import input_pairs,load_encoder,generate

def run(rows, lex, sem, ks=(5,10), lambdas=(0.5,0.75,1.0), thresholds=(0.0,0.4,0.6,0.8)):
    keys={(r["query_id"],r["candidate_id"]) for r in rows}
    if set(lex)!=keys or set(sem)!=keys: raise ValueError("score pair mismatch")
    gold={}
    by_q=defaultdict(list)
    for r in rows:
        q,c=r["query_id"],r["candidate_id"]
        v=r["answer_reusable"].strip().lower()
        if v not in ("true","false"):raise ValueError("missing provisional label")
        gold[(q,c)]=(v=="true")
        by_q[q].append(c)
    l=minmax_by_query(lex);s=minmax_by_query(sem)
    output=[]
    for k in ks:
        if k<1:raise ValueError("k must be >=1")
        for lam in lambdas:
            if not 0<=lam<=1:raise ValueError("lambda outside [0,1]")
            per=[]
            for q,cs in sorted(by_q.items()):
                stage1=sorted(cs,key=lambda c:(-lex[(q,c)],c))[:k]
                relevant=[c for c in cs if gold[(q,c)]]
                eligible=bool(relevant)
                recall=any(c in stage1 for c in relevant)
                ranked=sorted(stage1,key=lambda c:(-(lam*l[(q,c)]+(1-lam)*s[(q,c)]),c))
                winner=ranked[0]
                score=lam*l[(q,winner)]+(1-lam)*s[(q,winner)]
                rank=next((i for i,c in enumerate(ranked,1) if gold[(q,c)]),None)
                per.append(dict(query_id=q,eligible=eligible,stage1_recalled=recall,
                     first_positive_rank=rank,top_candidate_id=winner,
                     top_reusable=gold[(q,winner)],top_score=score))
            eligible=[p for p in per if p["eligible"]]
            for threshold in thresholds:
                if not 0<=threshold<=1:raise ValueError("threshold outside [0,1]")
                accepted=[p for p in per if p["top_score"]>=threshold]
                correct=sum(p["top_reusable"] for p in accepted)
                false=sum(not p["top_reusable"] for p in accepted)
                output.append(dict(k=k,lambda_lexical=lam,threshold=threshold,
                   queries=len(per),eligible_queries=len(eligible),
                   stage1_recall_eligible=sum(p["stage1_recalled"] for p in eligible)/len(eligible) if eligible else None,
                   hit_at_1_eligible=sum(p["first_positive_rank"]==1 for p in eligible)/len(eligible) if eligible else None,
                   mrr_eligible=sum(1/p["first_positive_rank"] for p in eligible if p["first_positive_rank"])/len(eligible) if eligible else None,
                   accepted=len(accepted),accepted_correct=correct,accepted_incorrect=false,
                   acceptance_coverage=len(accepted)/len(per) if per else None,
                   acceptance_precision=correct/len(accepted) if accepted else None,
                   false_accept_rate_all_queries=false/len(per) if per else None,
                   false_accept_rate_no_positive=sum(not p["top_reusable"] for p in accepted if not p["eligible"])/sum(not p["eligible"] for p in per) if any(not p["eligible"] for p in per) else None))
    return {"status":"EXPLORATORY_TWO_STAGE","warning":"Thresholds tuned here are not calibrated; provisional AI labels are not human approval. UNKNOWN label != no-reusable-answer.","configurations":output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",required=True)
    p.add_argument("--sem-root",default="../LLM_SEM")
    p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--device",default="cuda")
    p.add_argument("--output",default="results/two_stage_v0135879.json")
    a=p.parse_args()
    rows,questions,candidates=input_pairs(a.review)
    lex=lexical_scores(questions,candidates)
    encode=load_encoder(a.sem_root,a.checkpoint,a.tokenizer,a.device,"mean",.35)
    semrows=generate(rows,questions,candidates,encode)
    sem={(r["query_id"],r["candidate_id"]):float(r["score"]) for r in semrows}
    result=run(rows,lex,sem)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for x in result["configurations"]:
        print("K",x["k"],"lambda",x["lambda_lexical"],"threshold",x["threshold"],
              "recall",x["stage1_recall_eligible"],"MRR",x["mrr_eligible"],
              "accept",x["accepted"],"wrong",x["accepted_incorrect"])
    print("report:",out)
if __name__=="__main__":main()
