#!/usr/bin/env python3
"""v0.13.58.78 exploratory lexical + LLM_SEM mean retrieval fusion."""
import argparse, csv, json, math
from collections import Counter, defaultdict
from pathlib import Path
from score_holdout_llm_sem_v0135875 import input_pairs, generate, load_encoder
from compare_holdout_retrieval_v0135874 import evaluate
from diagnose_semantic_retrieval_v0135876 import diagnose

LAMBDAS=(0.,.25,.5,.75,1.)

def grams(s):
    s="".join(s.lower().split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def lexical_scores(queries,candidates):
    # IDF is fitted only on candidate questions; no answer labels consulted.
    vectors={c:grams(t) for c,t in candidates.items()}
    df=Counter()
    for v in vectors.values():df.update(v.keys())
    n=len(vectors)
    def weight(v):
        return {k:x*(math.log((n+1)/(df.get(k,0)+1))+1) for k,x in v.items()}
    cv={k:weight(v) for k,v in vectors.items()}
    qv={k:weight(grams(v)) for k,v in queries.items()}
    def norm(v):return math.sqrt(sum(x*x for x in v.values()))
    norms={k:norm(v) for k,v in cv.items()}
    result={}
    for q,v in qv.items():
        nv=norm(v)
        for c,w in cv.items():
            dot=sum(x*w.get(k,0) for k,x in v.items())
            result[(q,c)]=dot/(nv*norms[c]) if nv and norms[c] else 0.
    return result

def minmax_by_query(scores):
    groups=defaultdict(list)
    for (q,c),v in scores.items():
        if not math.isfinite(v):raise ValueError("nonfinite score")
        groups[q].append(v)
    bounds={q:(min(v),max(v)) for q,v in groups.items()}
    return {(q,c):(v-lo)/(hi-lo) if hi>lo else 0.
            for (q,c),v in scores.items() for lo,hi in [bounds[q]]}

def sweep(rows, lexical, semantic):
    keys={(r["query_id"],r["candidate_id"]) for r in rows}
    if set(lexical)!=keys or set(semantic)!=keys:raise ValueError("score pair mismatch")
    l=minmax_by_query(lexical);s=minmax_by_query(semantic)
    reports=[]
    for lam in LAMBDAS:
        ranking=[{"query_id":q,"candidate_id":c,
                  "score":str(lam*l[(q,c)]+(1-lam)*s[(q,c)])}
                 for q,c in sorted(keys)]
        e=evaluate(rows,ranking);d=diagnose(rows,ranking)
        reports.append({"lambda_lexical":lam,"hit_at_k_eligible":e["hit_at_k_eligible"],
                        "mrr_eligible":e["mrr_eligible"],
                        "mean_margin":d["per_query_margin"].get("mean"),
                        "top1_reusable_query_coverage":e["top1_reusable_query_coverage"]})
    return {"status":"EXPLORATORY_HYBRID_SWEEP","pair_count":len(keys),
            "normalization":"per-query min-max separately per modality",
            "warning":"Labels are provisional AI reviews. Tuning on this set invalidates independent-final claims.",
            "configurations":reports}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",required=True)
    p.add_argument("--sem-root",default="../LLM_SEM")
    p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--device",default="cuda")
    p.add_argument("--output",default="results/hybrid_retrieval_v0135878.json")
    a=p.parse_args()
    rows,queries,candidates=input_pairs(a.review)
    lex=lexical_scores(queries,candidates)
    enc=load_encoder(a.sem_root,a.checkpoint,a.tokenizer,a.device,"mean",0.35)
    semrows=generate(rows,queries,candidates,enc)
    sem={(r["query_id"],r["candidate_id"]):float(r["score"]) for r in semrows}
    report=sweep(rows,lex,sem)
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    for r in report["configurations"]:
        print("lambda",r["lambda_lexical"],"hits",r["hit_at_k_eligible"],
              "MRR",round(r["mrr_eligible"],4),"margin",round(r["mean_margin"],4))
    print("report:",target)
if __name__=="__main__":main()
