#!/usr/bin/env python3
"""v0.13.58.74: reproducible retrieval comparison; labels are provisional AI reviews.

Ranking CSV schema: query_id,candidate_id,score. Higher score ranks first.
Model ranking must be produced independently from the review labels.
"""
import argparse
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def evaluate(review_rows, ranking_rows):
    truth = {}
    qlabels = {}
    candidates = defaultdict(set)
    for row in review_rows:
        qid, cid = row["query_id"], row["candidate_id"]
        key = (qid, cid)
        if key in truth:
            raise ValueError("duplicate reviewed pair: "+str(key))
        val = row["answer_reusable"].strip().lower()
        if val not in ("true", "false"):
            raise ValueError("unreviewed pair: "+str(key))
        label = row["proposed_label"].strip().upper()
        if label not in ("KNOWN", "UNKNOWN"):
            raise ValueError("invalid query label")
        if qid in qlabels and qlabels[qid] != label:
            raise ValueError("inconsistent query label")
        truth[key] = val == "true"
        qlabels[qid] = label
        candidates[qid].add(cid)
    ranks = defaultdict(list)
    seen = set()
    for row in ranking_rows:
        qid, cid = row["query_id"], row["candidate_id"]
        key = (qid, cid)
        if key not in truth or key in seen:
            raise ValueError("unexpected or duplicate ranking pair: "+str(key))
        score = float(row["score"])
        if not (-float("inf") < score < float("inf")):
            raise ValueError("nonfinite score")
        seen.add(key)
        ranks[qid].append((cid,score))
    if set(truth) != seen:
        raise ValueError("ranking must cover all reviewed pairs")
    metrics = Counter()
    breakdown = []
    eligible = 0
    reciprocal = 0.0
    hits = {1:0,3:0,5:0}
    for qid in sorted(candidates):
        ordered = sorted(ranks[qid],key=lambda x:(-x[1],x[0]))
        relevant = {cid for cid in candidates[qid] if truth[(qid,cid)]}
        first = next((i for i,(cid,_) in enumerate(ordered,1) if cid in relevant), None)
        if relevant:
            eligible += 1
            reciprocal += 1/first
            for k in hits: hits[k] += first <= k
        best, score = ordered[0]
        label = qlabels[qid]
        metrics["top1_reusable"] += truth[(qid,best)]
        metrics["unknown_queries"] += label == "UNKNOWN"
        metrics["unknown_top1_reusable"] += label == "UNKNOWN" and truth[(qid,best)]
        breakdown.append({"query_id":qid,"proposed_label":label,
            "first_reusable_rank":first,"top1_candidate_id":best,
            "top1_score":score,"top1_reusable":truth[(qid,best)]})
    n = len(candidates)
    return {"status":"PROVISIONAL_AI_LABEL_EVALUATION","queries":n,
        "reviewed_pairs":len(truth),"eligible_queries":eligible,
        "oracle_query_coverage":eligible/n if n else None,
        "hit_at_k_eligible":{str(k):hits[k]/eligible if eligible else None for k in hits},
        "mrr_eligible":reciprocal/eligible if eligible else None,
        "top1_reusable_query_coverage":metrics["top1_reusable"]/n if n else None,
        "unknown_top1_reusable_count":metrics["unknown_top1_reusable"],
        "unknown_queries":metrics["unknown_queries"],
        "warning":"Reference-label agreement is NOT runtime gate precision or independent human approval.",
        "per_query":breakdown}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",required=True)
    p.add_argument("--ranking",required=True,help="Independent model scores: query_id,candidate_id,score")
    p.add_argument("--output",default="results/holdout_retrieval_v0135874.json")
    args=p.parse_args()
    report=evaluate(read_csv(args.review),read_csv(args.ranking))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="per_query"},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
