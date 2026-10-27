"""v0.13.41 blinded human candidate quality audit (offline, no model inference).

prepare: randomize 5 candidates per dialogue without showing NLL, rank or reference.
analyze: require completed human labels, then unblind and compute selection/oracle rates.
Never auto-fill human scores or treat string overlap as human quality.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

FIELDS=("context_fit","japanese_fluency","question_response","topic_continuity")

def stable_id(case_index,candidate_index):
    return hashlib.sha256(f"rpc-v01341:{case_index}:{candidate_index}".encode()).hexdigest()[:16]

def prepare(report,seed=1341):
    items=[]; mapping={}
    for ci,case in enumerate(report["details"]):
        for cand in case["candidates"]:
            idx=int(cand["index"]); uid=stable_id(ci,idx)
            mapping[uid]={"case_index":ci,"candidate_index":idx}
            items.append({"item_id":uid,"dialogue_id":case["dialogue_id"],
                          "history":case["prompt"],"answer":cand["text"],
                          "scores":{field:None for field in FIELDS},
                          "reviewer":"", "review_note":""})
    random.Random(seed).shuffle(items)
    return items,mapping

def validate_labels(items,mapping):
    seen=set()
    for row in items:
        uid=row.get("item_id")
        if uid not in mapping or uid in seen:
            raise ValueError(f"unknown/duplicate item_id: {uid}")
        seen.add(uid)
        if not str(row.get("reviewer","")).strip():
            raise ValueError(f"missing reviewer: {uid}")
        values=row.get("scores",{})
        for field in FIELDS:
            v=values.get(field)
            if type(v) is not int or v not in range(4):
                raise ValueError(f"invalid {field} for {uid}; use integer 0..3")
    if seen!=set(mapping):raise ValueError("incomplete audit: all candidates required")

def qualified(scores):
    return scores["context_fit"]>=2 and scores["japanese_fluency"]>=2 and scores["topic_continuity"]>=2 and scores["question_response"]>=2

def analyze(report,items,mapping):
    validate_labels(items,mapping)
    labeled={row["item_id"]:row for row in items}
    per_case=[]
    for ci,case in enumerate(report["details"]):
        candidate_labels={c["index"]:labeled[stable_id(ci,c["index"])]["scores"]
                          for c in case["candidates"]}
        selected=case["selected_index"]
        passing=[idx for idx,s in candidate_labels.items() if qualified(s)]
        per_case.append({"dialogue_id":case["dialogue_id"],
                         "candidate_count":len(candidate_labels),
                         "first_qualified":0 in passing,
                         "selected_qualified":selected in passing,
                         "human_oracle_exists":bool(passing),
                         "selected_is_human_best":sum(candidate_labels[selected].values())==
                           max(sum(s.values()) for s in candidate_labels.values()),
                         "selected_context_fit":candidate_labels[selected]["context_fit"],
                         "max_context_fit":max(s["context_fit"] for s in candidate_labels.values()),
                         "qualified_candidate_indices":passing})
    n=len(per_case)
    return {"version":"v0.13.41","status":"HUMAN_AUDIT_COMPLETED",
            "cases":n,"candidates":len(items),
            "human_oracle_cases":sum(x["human_oracle_exists"] for x in per_case),
            "selected_qualified_cases":sum(x["selected_qualified"] for x in per_case),
            "first_qualified_cases":sum(x["first_qualified"] for x in per_case),
            "selected_best_sum_cases":sum(x["selected_is_human_best"] for x in per_case),
            "ranking_misses_with_qualified_candidate":sum(x["human_oracle_exists"] and not x["selected_qualified"] for x in per_case),
            "generation_failures_no_qualified_candidate":sum(not x["human_oracle_exists"] for x in per_case),
            "cases_detail":per_case,
            "notes":["All scores are manual; reference answers and model metrics were hidden from review items.",
                     "Qualified requires all four human scores >=2/3; the threshold is a prespecified heuristic.",
                     "This validation review cannot establish independent final test performance.",
                     "Does not modify production or approve semantic knowledge."]}

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_new(path,obj):
    path=Path(path)
    if path.exists():raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("prepare")
    a.add_argument("--source",default="results/rpc_response_ranking_v01340.json")
    a.add_argument("--review",default="results/rpc_candidate_review_v01341.json")
    a.add_argument("--key",default="results/rpc_candidate_review_key_v01341.json")
    a.add_argument("--seed",type=int,default=1341)
    b=sub.add_parser("analyze")
    b.add_argument("--source",default="results/rpc_response_ranking_v01340.json")
    b.add_argument("--review",default="results/rpc_candidate_review_v01341.json")
    b.add_argument("--key",default="results/rpc_candidate_review_key_v01341.json")
    b.add_argument("--output",default="results/rpc_candidate_audit_v01341.json")
    args=p.parse_args()
    report=read_json(args.source)
    if report.get("version")!="v0.13.40":p.error("expected v0.13.40 source")
    if args.command=="prepare":
        if Path(args.review).exists() or Path(args.key).exists():p.error("review/key exists; refusing to overwrite")
        items,mapping=prepare(report,args.seed)
        write_new(args.review,{"version":"v0.13.41","instructions":"Manual 0=poor,1=weak,2=acceptable,3=good. Fill all four scores and reviewer. Do not refer to ranking or reference.", "items":items})
        write_new(args.key,{"version":"v0.13.41","mapping":mapping})
        print("REVIEW_PENDING",len(items),"items; review:",args.review)
    else:
        reviewed=read_json(args.review);key=read_json(args.key)
        result=analyze(report,reviewed["items"],key["mapping"])
        write_new(args.output,result)
        print(json.dumps({k:v for k,v in result.items() if k!="cases_detail"},ensure_ascii=False,indent=2))
        print("report:",args.output)

if __name__=="__main__":main()
