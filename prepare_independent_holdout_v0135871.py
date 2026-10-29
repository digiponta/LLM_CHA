"""v0.13.58.71: locked protocol for independently authored holdout questions.

Create question/label template BEFORE model execution; human attestation
required. Results do not prove independence; declaration is auditable.
Do not tune rules or thresholds on this evaluation set.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from collections import Counter

FIELDS=["id","question","expected","review_status","independence_attested","review_notes"]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(p):
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        # Blank template: independent questions must be authored by reviewer,
        # not algorithm developer after observing retrieval behavior.
        for i in range(1,25):
            w.writerow({"id":f"holdout71-{i:03d}","question":"",
             "expected":"","review_status":"PENDING","independence_attested":"NO",
             "review_notes":"Independent human-authored question. KNOWN iff reusable answer exists in all 56 training records."})
    print("template:",p)

def validate(path,source):
    with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if len(rows)<12:raise ValueError("need >=12 independently authored questions")
    ids=set();qset=set()
    from train_daily_generation_v0135847 import dataset
    from retrieve_question_top3_v0135861 import norm
    train,old,_=dataset(source)
    forbidden={norm(x["user"]) for x in train+old}
    for r in rows:
        if r["id"] in ids:raise ValueError("duplicate ID")
        ids.add(r["id"])
        q=norm(r["question"])
        if not q or q in qset or q in forbidden:raise ValueError(f'blank/duplicate/exposed question: {r["id"]}')
        qset.add(q)
        if r["expected"] not in ("KNOWN","UNKNOWN"):raise ValueError("missing class label")
        if r["review_status"]!="APPROVED" or r["independence_attested"]!="YES":
            raise ValueError(f'review or independence pending: {r["id"]}')
    if len(set(r["expected"] for r in rows))!=2:raise ValueError("both classes needed")
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--cases",type=Path,default=Path("data/independent_holdout_v0135871.csv"))
    p.add_argument("--output",type=Path,default=Path("results/holdout71_lock.json"))
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--lock",action="store_true")
    a=p.parse_args()
    if a.prepare:return prepare(a.cases)
    if not a.lock:p.error("use --prepare or --lock")
    if a.output.exists():raise FileExistsError(a.output)
    rows=validate(a.cases,a.source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    lock={"version":"v0.13.58.71","protocol":"PRE-REGISTERED_QUESTION_CLASS_ONLY",
      "question_count":len(rows),"class_counts":dict(Counter(r["expected"] for r in rows)),
      "cases_sha256":digest(a.cases),"source_sha256":digest(a.source),
      "threshold":.88,"margin":0,"fixed_before_evaluation":True,
      "independence_is_self_attested":True,
      "caveat":"Question-level KNOWN labels do not establish candidate answer correctness. Requires independent answer-level review."}
    a.output.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(lock,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
