"""v0.13.58.72: auditable holdout label inspection before lock.

Generates an all-56 training question+answer review worksheet for each holdout
query. No model inference; human reviewers decide whether an answer is reusable.
Never auto-approve or claim independence for assistant-authored questions.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from collections import defaultdict
from train_daily_generation_v0135847 import dataset
from retrieve_question_top3_v0135861 import norm

REVIEW_COLS=["query_id","query","proposed_label","candidate_id","candidate_question",
             "candidate_answer","answer_reusable","review_status","review_notes"]

def read_cases(p):
    with p.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if not rows:raise ValueError("empty cases")
    for r in rows:
        if not r.get("id") or not r.get("question","").strip():raise ValueError("blank question or ID")
        if r.get("expected") not in ("KNOWN","UNKNOWN"):raise ValueError("missing provisional label")
    if len({r["id"] for r in rows})!=len(rows):raise ValueError("duplicate IDs")
    return rows

def check_overlap(cases,train,old):
    seen={}
    known={norm(x["user"]):x["id"] for x in train}
    previously={norm(x["user"]):x["id"] for x in old}
    results=[]
    for r in cases:
        n=norm(r["question"])
        flags=[]
        if n in seen:flags.append("DUPLICATE_HOLDOUT")
        if n in known:flags.append("TRAIN_EXACT")
        if n in previously:flags.append("PREVIOUS_HOLDOUT_EXACT")
        results.append({"id":r["id"],"question":r["question"],"flags":flags,
                        "matched_id":known.get(n) or previously.get(n)})
        seen[n]=r["id"]
    return results

def prepare(cases,train,output):
    if output.exists():raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=REVIEW_COLS);w.writeheader()
        for q in cases:
            for t in train:
                w.writerow({"query_id":q["id"],"query":q["question"],
                    "proposed_label":q["expected"],"candidate_id":t["id"],
                    "candidate_question":t["user"],"candidate_answer":t["assistant"],
                    "answer_reusable":"","review_status":"PENDING",
                    "review_notes":"Review full answer reuse, not topic similarity"})
    return len(cases)*len(train)

def assess(cases,review,train):
    expected_count=len(train)
    expected_ids={r["id"] for r in train}
    groups=defaultdict(list)
    for r in review:groups[r["query_id"]].append(r)
    out=[]
    for q in cases:
        items=groups.get(q["id"],[])
        ids={r["candidate_id"] for r in items}
        complete=(len(items)==expected_count and ids==expected_ids and
             all(r["review_status"]=="APPROVED" and r["answer_reusable"] in ("YES","NO") for r in items))
        reusable=[r["candidate_id"] for r in items if r["review_status"]=="APPROVED" and r["answer_reusable"]=="YES"]
        final=("KNOWN" if reusable else "UNKNOWN") if complete else "UNDETERMINED"
        out.append({"id":q["id"],"proposed":q["expected"],"verified":final,
                    "complete":complete,"reviewed":sum(r["review_status"]=="APPROVED" for r in items),
                    "total":expected_count,"reusable_ids":reusable,
                    "label_agrees":q["expected"]==final if complete else None})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cases",type=Path,default=Path("data/independent_holdout_v0135871.csv"))
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--worksheet",type=Path,default=Path("data/holdout_answer_review_v0135872.csv"))
    p.add_argument("--report",type=Path,default=Path("results/holdout_label_audit_v0135872.json"))
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--assess",action="store_true")
    a=p.parse_args()
    cases=read_cases(a.cases)
    train,old,_=dataset(a.source)
    duplicates=check_overlap(cases,train,old)
    if a.prepare:
        count=prepare(cases,train,a.worksheet)
        print(json.dumps({"count":count,"worksheet":str(a.worksheet),"exact_overlap_flags":sum(bool(x["flags"]) for x in duplicates)},ensure_ascii=False))
        return
    if not a.assess:p.error("choose --prepare or --assess")
    if a.report.exists():raise FileExistsError(a.report)
    if not a.worksheet.exists():raise FileNotFoundError(a.worksheet)
    with a.worksheet.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    evaluation=assess(cases,rows,train)
    report={"version":"v0.13.58.72","question_count":len(cases),"training_count":len(train),
      "source_sha256":hashlib.sha256(a.source.read_bytes()).hexdigest(),
      "case_sha256":hashlib.sha256(a.cases.read_bytes()).hexdigest(),
      "assistant_authored_holdout_independent_human_authorship":False,
      "no_auto_approval":True,"overlaps":duplicates,"labels":evaluation}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":str(a.report),"complete":sum(x["complete"] for x in evaluation),
      "undetermined":sum(not x["complete"] for x in evaluation),
      "label_disagreements":sum(x["label_agrees"] is False for x in evaluation),
      "exact_overlaps":sum(bool(x["flags"]) for x in duplicates)},ensure_ascii=False))
if __name__=="__main__":main()
