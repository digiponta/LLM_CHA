"""LLM_CHA v0.4.0 review scoring; never auto-promote persona facts."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from persona_review_v0378 import review_rows, VERDICTS

FIELDS=("id","line","segment","original","subject","means","predicate","marker")
def score(corpus, review_csv):
    candidates=review_rows(corpus)
    with Path(review_csv).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required=set(FIELDS)|{"verdict","note"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("review columns missing")
        reviewed=list(reader)
    if len(reviewed)!=len(candidates):
        raise ValueError("review row count differs from current source")
    by_id={}
    for row in reviewed:
        identifier=row["id"]
        if identifier in by_id:raise ValueError("duplicate candidate ID")
        by_id[identifier]=row
    if set(by_id)!={row["id"] for row in candidates}:
        raise ValueError("review IDs do not match current corpus")
    counts={v:0 for v in VERDICTS}
    pending=0
    accepted=[]
    for canonical in candidates:
        row=by_id[canonical["id"]]
        if any(str(row[k])!=str(canonical[k]) for k in FIELDS):
            raise ValueError("candidate source or semantic roles were edited")
        verdict=row["verdict"].strip().upper()
        if verdict=="UNREVIEWED":
            pending+=1
        elif verdict in counts:
            counts[verdict]+=1
            if verdict=="CORRECT":
                accepted.append({k:canonical[k] for k in FIELDS})
        else:
            raise ValueError(f"invalid verdict: {verdict!r}")
    n=sum(counts.values())
    return {"version":"v0.4.0","candidate_count":len(candidates),"reviewed":n,
            "unreviewed":pending,**{v.lower():counts[v] for v in VERDICTS},
            "precision_reviewed":counts["CORRECT"]/n if n else None,
            "precision_all_candidates":counts["CORRECT"]/len(candidates) if not pending and candidates else None,
            "accepted_count":len(accepted),"accepted_for_future_review_only":accepted,
            "runtime_enabled":False,"truth_promotions":0}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/data-nagato.txt")
    p.add_argument("--csv",default="results/persona_review_v0378.csv")
    p.add_argument("--report",default="results/persona_review_scored_v0400.json")
    a=p.parse_args()
    result=score(a.corpus,a.csv)
    out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="accepted_for_future_review_only"},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
