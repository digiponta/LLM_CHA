"""Retrieval evaluation: dev-only annotations; no final independent benchmark claims."""
import argparse,csv,json
from pathlib import Path
from retrieve_question_top3_v0135861 import retrieve,norm
from train_daily_generation_v0135847 import dataset

def rank_nonzero(train,question,method="tfidf",ngram=2,k=3):
    hits=retrieve(train,question,ngram,method,k=len(train))
    return [h for h in hits if h["score"]>0][:k]

def evaluate(train,queries,labels,method="tfidf",ngram=2,threshold=0):
    """labels: query id -> set of relevant train ids; empty means Unknown.
    All labels must be independently reviewed; no gold guessed from lexical scores.
    """
    if threshold<0 or threshold>1:raise ValueError("threshold")
    if len({r["id"] for r in train})!=len(train):raise ValueError("duplicate training IDs")
    known={r["id"] for r in train}
    query_ids={q["id"] for q in queries}
    if set(labels)!=query_ids:raise ValueError("every query must be labeled")
    for qid,gold in labels.items():
        if not gold<=known:raise ValueError(f"invalid target ID for {qid}")
    rows=[]
    for q in queries:
        ranked=rank_nonzero(train,q["user"],method,ngram,3)
        hits=[h for h in ranked if h["score"]>=threshold]
        gold=labels[q["id"]]
        first=next((i+1 for i,h in enumerate(hits) if h["id"] in gold),None)
        rows.append({"id":q["id"],"question":q["user"],"gold":sorted(gold),
            "top3":hits,"known":bool(gold),"first_relevant_rank":first,
            "top1_correct":bool(hits and hits[0]["id"] in gold),
            "recall3":bool(first),"rr":1/first if first else 0,
            "unknown_rejected":not hits if not gold else None,
            "false_accept":bool(hits) if not gold else None})
    k=[r for r in rows if r["known"]];u=[r for r in rows if not r["known"]]
    safe=lambda seq:sum(seq)/len(seq) if seq else None
    return {"method":method,"ngram":ngram,"threshold":threshold,"known_count":len(k),
       "unknown_count":len(u),"top1_accuracy":safe([r["top1_correct"] for r in k]),
       "recall_at_3":safe([r["recall3"] for r in k]),
       "mrr_at_3":safe([r["rr"] for r in k]),
       "unknown_reject_rate":safe([r["unknown_rejected"] for r in u]),
       "unknown_false_accept_rate":safe([r["false_accept"] for r in u]),
       "rows":rows}

def export_annotations(source,output):
    if output.exists():raise FileExistsError(output)
    train,holdout,_=dataset(source)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["holdout_id","holdout_question","relevant_training_ids",
                                         "review_status","review_notes"])
        w.writeheader()
        for q in holdout:
            w.writerow({"holdout_id":q["id"],"holdout_question":q["user"],
                        "relevant_training_ids":"","review_status":"PENDING",
                        "review_notes":"IDs separated by semicolon; NONE for verified unknown"})
    print(f"Review template: {output} ({len(holdout)} queries); training pool {len(train)}")

def read_labels(path,queries):
    with path.open(newline="",encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
    if len(rows)!=len(queries):raise ValueError("annotation count mismatch")
    result={}
    expected={q["id"]:norm(q["user"]) for q in queries}
    for row in rows:
        qid=row["holdout_id"]
        if qid not in expected or qid in result:raise ValueError("unexpected/duplicated query ID")
        if norm(row["holdout_question"])!=expected[qid]:raise ValueError("question altered")
        if row["review_status"].strip().upper()!="APPROVED":
            raise ValueError(f"{qid}: review is not APPROVED")
        ids=row["relevant_training_ids"].strip()
        if not ids:raise ValueError(f"{qid}: missing gold IDs or NONE")
        result[qid]=set() if ids.upper()=="NONE" else {x.strip() for x in ids.split(";") if x.strip()}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--annotations",type=Path,default=Path("data/retrieval_dev_labels_v0135862.csv"))
    p.add_argument("--output",type=Path,default=Path("results/retrieval_eval_v0135862.json"))
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--threshold",type=float,default=0)
    a=p.parse_args()
    if a.prepare:return export_annotations(a.source,a.annotations)
    train,holdout,_=dataset(a.source)
    labels=read_labels(a.annotations,holdout)
    reports=[evaluate(train,holdout,labels,method,n,a.threshold)
             for method in ("count","tfidf") for n in (2,3)]
    payload={"version":"v0.13.58.62","evaluation_split":"DEVELOPMENT_REUSED_HOLDOUT",
       "independent_final_test":False,"labels_human_reviewed":True,
       "threshold_was_calibrated_on_dev":a.threshold!=0,
       "reports":reports,"production_approved":False}
    if a.output.exists():raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for x in reports:
        print(json.dumps({k:v for k,v in x.items() if k!="rows"},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
