"""v0.13.58.67: build independent candidate answer-reuse review.

The 16-question development split is NOT an independent test.
Review candidate *answers*, not just matching topics. Never approve labels automatically.
"""
import argparse,csv,json
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from compare_japanese_semantic_v0135863 import MODEL,MODES,topk
from rerank_question_intent_v0135864 import rerank

COLUMNS=["query_id","query","proposed_class","original_class","rank","candidate_id",
         "candidate_question","candidate_answer","base_score","adjusted_score",
         "intent_conflict","valence_conflict","answer_reusable","review_status","review_notes"]
def read_proposals(path):
    with path.open(newline="",encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
    ids=set()
    for r in rows:
        if r["id"] in ids:raise ValueError("duplicate id")
        ids.add(r["id"])
        if r["expected"] not in ("KNOWN","UNKNOWN"):raise ValueError("bad proposed class")
        if not r["question"].strip():raise ValueError("blank question")
    if not rows:raise ValueError("empty proposals")
    return rows
def create_review(cases,train,hits,output):
    if output.exists():raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader()
        for q,ranked in zip(cases,hits):
            for h in ranked[:10]:
                w.writerow({"query_id":q["id"],"query":q["question"],
                  "proposed_class":q["expected"],"original_class":q["expected"],
                  "rank":h["rank"],"candidate_id":h["id"],"candidate_question":h["question"],
                  "candidate_answer":h["answer"],"base_score":h["score"],
                  "adjusted_score":h["adjusted_score"],
                  "intent_conflict":h["intent_conflict"],"valence_conflict":h["valence_conflict"],
                  "answer_reusable":"","review_status":"PENDING",
                  "review_notes":"Mark YES only when this answer is safe and appropriate for the query; else NO"})
def assess(rows):
    """Approved records only. Missing reviews do not count as negative."""
    byid={}
    for r in rows:
        qid=r["query_id"];byid.setdefault(qid,[]).append(r)
    output=[]
    for qid,items in byid.items():
        if len({r["candidate_id"] for r in items})!=len(items):raise ValueError(f"duplicate candidate {qid}")
        approvals=[r for r in items if r["review_status"]=="APPROVED"]
        bad=[r for r in approvals if r["answer_reusable"] not in ("YES","NO")]
        if bad:raise ValueError(f"invalid approval of {qid}")
        complete=len(approvals)==len(items)
        accepted=[r for r in approvals if r["answer_reusable"]=="YES"]
        top=items[0]
        output.append({"query_id":qid,"query":top["query"],"proposal":top["proposed_class"],
            "reviewed":len(approvals),"total_candidates":len(items),"review_complete":complete,
            "approved_reusable_candidate_ids":[r["candidate_id"] for r in accepted],
            "verified_class":("KNOWN" if accepted else "UNKNOWN") if complete else "UNDETERMINED",
            "top1_answer_reusable":top["review_status"]=="APPROVED" and top["answer_reusable"]=="YES"
               if top["review_status"]=="APPROVED" else None})
    return output
def run(args):
    cases=read_proposals(args.cases)
    if args.assess:
        with args.review.open(newline="",encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
        info=assess(rows)
        # A reviewed Top-10 with zero hits is NOT enough to claim no reusable
        # answers exist among 56. Avoid incorrectly certifying UNKNOWN.
        for x in info:
            if x["verified_class"]=="UNKNOWN":
                x["verified_class"]="NO_REUSABLE_IN_REVIEWED_TOP10"
        if args.output.exists():raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({"version":"v0.13.58.67","development_only":True,
               "not_independent":True,"queries":info,"all_56_reviewed":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(info,ensure_ascii=False,indent=2));return
    train,_,_=dataset(args.source)
    if len(train)!=56:raise ValueError("requires 56 training records")
    import torch
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer(MODEL,device="cpu" if args.cpu or not torch.cuda.is_available() else "cuda",trust_remote_code=False)
    qp,dp=MODES["semantic"]
    ix=model.encode([dp+r["user"] for r in train],normalize_embeddings=True)
    qv=model.encode([qp+r["question"] for r in cases],normalize_embeddings=True)
    hits=[rerank(q["question"],c) for q,c in zip(cases,topk(qv,ix,train,k=56))]
    create_review(cases,train,hits,args.review)
    print(f"Created answer review for {len(cases)} questions: {args.review}")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--cases",type=Path,default=Path("data/unknown_gate_dev_v0135866.csv"))
    p.add_argument("--review",type=Path,default=Path("data/answer_reuse_review_v0135867.csv"))
    p.add_argument("--output",type=Path,default=Path("results/answer_reuse_v0135867.json"))
    p.add_argument("--assess",action="store_true")
    p.add_argument("--cpu",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()
