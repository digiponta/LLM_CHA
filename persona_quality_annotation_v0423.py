"""v0.4.23 human annotation pipeline for real, untouched runtime answers.

Input: captured JSONL of actual runs; no generation or model changes.
Holdout status is provenance-dependent, never inferred from labels alone.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from persona_quality_benchmark_v0422 import score

FIELDS={"id","question","answer","agreement","semantic_agreement","runtime_accepted"}
def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def prepare(records, *, excluded_questions=(), excluded_pairs=()):
    excluded_q={_digest(q.strip()) for q in excluded_questions}
    excluded_p={_digest(q.strip()+"\x00"+a.strip()) for q,a in excluded_pairs}
    rows=[];ids=set();discarded=0
    for r in records:
        if not isinstance(r,dict) or set(r)!=FIELDS:raise ValueError("capture schema")
        if not isinstance(r["id"],str) or not r["id"].strip() or r["id"] in ids:
            raise ValueError("duplicate/invalid id")
        ids.add(r["id"])
        if any(not isinstance(r[k],str) for k in ("question","answer")):
            raise ValueError("text fields")
        if not r["question"].strip():raise ValueError("empty question")
        for key in ("agreement","semantic_agreement"):
            if type(r[key]) not in (float,int) or not 0<=r[key]<=1:raise ValueError(key)
        if type(r["runtime_accepted"]) is not bool:raise ValueError("runtime_accepted")
        q=r["question"].strip();a=r["answer"].strip()
        if _digest(q) in excluded_q or _digest(q+"\x00"+a) in excluded_p:
            discarded+=1;continue
        rows.append({**r,"gold_inappropriate":None,"label_source":"UNLABELED",
                     "split":"pending_review"})
    return {"version":"v0.4.23","status":"UNLABELED","rows":rows,
            "excluded":discarded,"independent_holdout_claimed":False,
            "dataset_sha256":_digest("\n".join(json.dumps(r,sort_keys=True,ensure_ascii=False)
                                                for r in rows))}

def apply_annotations(prepared, annotations, *, split="development"):
    if prepared.get("status")!="UNLABELED" or split not in ("development","holdout"):
        raise ValueError("invalid prepared dataset or split")
    by_id={}
    for a in annotations:
        if not isinstance(a,dict) or set(a)!={"id","gold_inappropriate","reviewer"}:
            raise ValueError("annotation schema")
        if not isinstance(a["id"],str) or a["id"] in by_id or not a["id"]:
            raise ValueError("duplicate annotation")
        if type(a["gold_inappropriate"]) is not bool or not isinstance(a["reviewer"],str) or not a["reviewer"].strip():
            raise ValueError("human review required")
        by_id[a["id"]]=a
    if set(by_id)!={r["id"] for r in prepared["rows"]}:
        raise ValueError("annotations must match all sample ids")
    labeled=[]
    for r in prepared["rows"]:
        row={k:r[k] for k in FIELDS}
        row.update(split=split, gold_inappropriate=by_id[r["id"]]["gold_inappropriate"],
                   label_source="HUMAN_REVIEW")
        labeled.append(row)
    return labeled

def load_jsonl(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>2_000_000:raise ValueError("bad file")
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--captures",required=True)
    parser.add_argument("--prepared",required=True)
    parser.add_argument("--annotations")
    parser.add_argument("--labeled")
    parser.add_argument("--split",choices=("development","holdout"),default="development")
    a=parser.parse_args()
    try:
        # Exclusions are anchored to historical, already-used development examples.
        exclude=("今日は何をしていたの","貴方は誰","あなたは誰ですか","長門",
                 "化学とは","CPUとは","貴方は","あなたの")
        prepared=prepare(load_jsonl(a.captures),excluded_questions=exclude)
        Path(a.prepared).write_text(json.dumps(prepared,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({k:v for k,v in prepared.items() if k!="rows"} |
                         {"prepared_count":len(prepared["rows"])},ensure_ascii=False,indent=2))
        if a.annotations:
            if not a.labeled:raise ValueError("--labeled required with --annotations")
            labeled=apply_annotations(prepared,load_jsonl(a.annotations),split=a.split)
            Path(a.labeled).write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in labeled),encoding="utf-8")
            print(json.dumps(score(labeled,split=a.split),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        parser.exit(1,f"annotation pipeline failed: {exc}\n")
if __name__=="__main__":main()
