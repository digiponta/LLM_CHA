"""v0.4.22 gold-labeled quality benchmark; evaluation only, no runtime edits.

Rows are JSONL. Gold label is whether the ANSWER is inappropriate (not
whether the runtime accepted it). Frozen shadow warnings predict this label.
Development fixtures are never counted as independent holdout evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from persona_response_shadow_v0421 import evaluate

REQUIRED={"id","split","question","answer","gold_inappropriate",
          "agreement","semantic_agreement","runtime_accepted","label_source"}
SPLITS={"development","holdout"}
def validate(row):
    if not isinstance(row,dict) or set(row)!=REQUIRED:raise ValueError("invalid row schema")
    if not isinstance(row["id"],str) or not row["id"].strip():raise ValueError("id")
    if row["split"] not in SPLITS:raise ValueError("split")
    if not isinstance(row["question"],str) or not row["question"].strip():raise ValueError("question")
    if not isinstance(row["answer"],str):raise ValueError("answer")
    for key in ("gold_inappropriate","runtime_accepted"):
        if type(row[key]) is not bool:raise ValueError(key)
    for key in ("agreement","semantic_agreement"):
        if type(row[key]) not in (float,int) or not 0<=row[key]<=1:raise ValueError(key)
    if row["label_source"] not in ("HUMAN_REVIEW","DEVELOPMENT_EXAMPLE"):
        raise ValueError("label_source")
    if row["split"]=="holdout" and row["label_source"]!="HUMAN_REVIEW":
        raise ValueError("holdout must be human-reviewed")
    return row

def score(rows, *, split):
    if split not in SPLITS:raise ValueError("split")
    tp=fp=tn=fn=0
    seen=set()
    for row in rows:
        validate(row)
        if row["id"] in seen:raise ValueError("duplicate id")
        seen.add(row["id"])
        if row["split"]!=split:continue
        shadow=evaluate(row["question"],row["answer"],
                        agreement=row["agreement"],
                        semantic_agreement=row["semantic_agreement"],
                        accepted=row["runtime_accepted"])
        predicted=shadow["needs_review"]
        actual=row["gold_inappropriate"]
        if predicted and actual:tp+=1
        elif predicted and not actual:fp+=1
        elif not predicted and actual:fn+=1
        else:tn+=1
    count=tp+fp+tn+fn
    def ratio(a,b):return a/b if b else None
    return {"version":"v0.4.22","split":split,"count":count,
            "benchmark_status":"EVALUATED" if count else "NO_LABELED_SAMPLES",
            "independent_holdout_claimed":False,
            "tp":tp,"fp":fp,"tn":tn,"fn":fn,
            "precision":ratio(tp,tp+fp),"recall":ratio(tp,tp+fn),
            "false_positive_rate":ratio(fp,fp+tn),
            "false_negative_rate":ratio(fn,fn+tp),
            "accuracy":ratio(tp+tn,count),
            "runtime_decisions_modified":False,"training_enabled":False}

def load_jsonl(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>2_000_000:raise ValueError("invalid dataset")
    rows=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():rows.append(validate(json.loads(line)))
    if len(rows)>10000:raise ValueError("too many rows")
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",required=True)
    ap.add_argument("--split",required=True,choices=sorted(SPLITS))
    args=ap.parse_args()
    try:print(json.dumps(score(load_jsonl(args.dataset),split=args.split),
                         ensure_ascii=False,indent=2))
    except (ValueError,TypeError,OSError,json.JSONDecodeError) as exc:
        ap.exit(1,f"benchmark failed: {exc}\n")
if __name__=="__main__":main()
