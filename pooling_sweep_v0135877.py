#!/usr/bin/env python3
"""v0.13.58.77 — exploratory pooling sweep, no checkpoint training.

IMPORTANT: selecting the best configuration on this holdout makes this set
development data, not an independent final test.
"""
import argparse,csv,json
from pathlib import Path
from score_holdout_llm_sem_v0135875 import input_pairs,load_encoder,generate
from compare_holdout_retrieval_v0135874 import evaluate
from diagnose_semantic_retrieval_v0135876 import diagnose

CONFIGS=[("mean",0.35),("last",0.35),("attention",0.35),
         ("hybrid",0.0),("hybrid",0.35),("hybrid",0.5),
         ("hybrid",0.75),("hybrid",1.0)]

def run_sweep(rows,queries,candidates,encoder_factory):
    reports=[]
    for pooling,alpha in CONFIGS:
        encode=encoder_factory(pooling,alpha)
        ranking=generate(rows,queries,candidates,encode)
        e=evaluate(rows,ranking)
        d=diagnose(rows,ranking)
        reports.append({"pooling":pooling,"alpha":alpha if pooling=="hybrid" else None,
          "hit_at_k_eligible":e["hit_at_k_eligible"],"mrr_eligible":e["mrr_eligible"],
          "positive_beats_all_negative_queries":d["positive_beats_all_negative_queries"],
          "mean_margin":d["per_query_margin"].get("mean"),
          "positive_mean":d["positive_scores"].get("mean"),
          "negative_mean":d["negative_scores"].get("mean")})
    return {"status":"EXPLORATORY_HOLDOUT_POOLING_SWEEP",
            "warning":"Do NOT claim independent final holdout performance after selecting on these labels.",
            "configurations":reports}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review",required=True)
    p.add_argument("--sem-root",default="../LLM_SEM")
    p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--device",default="cuda")
    p.add_argument("--output",default="results/pooling_sweep_v0135877.json")
    args=p.parse_args()
    rows,questions,candidates=input_pairs(args.review)
    # Reuse existing real checkpoint-backed encoder API.
    def factory(pooling,alpha):
        return load_encoder(args.sem_root,args.checkpoint,args.tokenizer,args.device,pooling,alpha)
    result=run_sweep(rows,questions,candidates,factory)
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in result["configurations"]:
        print(r["pooling"],r["alpha"],r["hit_at_k_eligible"],"MRR",round(r["mrr_eligible"],4),
              "margin",round(r["mean_margin"],4))
    print("report:",dest)

if __name__=="__main__":main()
