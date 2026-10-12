"""v0.3.7.0 conservative raw-corpus evidence review.

Read-only: sentence excerpts are not automatically promoted or treated as facts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

UNCERTAINTY=("かもしれない","可能性","に違いない","多分","仮定","もし","とすると","ではないか","思う","考える","だろう")
SEPARATORS=("。","！","？")

def split_sentences(line):
    fragments=[line]
    for delim in SEPARATORS:
        fragments=[part for text in fragments for part in text.split(delim)]
    return [fragment.strip() for fragment in fragments if fragment.strip()]

def collect(source,concept,limit=30):
    if not concept or not concept.strip():raise ValueError("concept required")
    if limit<1:raise ValueError("limit must be positive")
    path=Path(source)
    text=path.read_text(encoding="utf-8-sig")
    out=[]
    for line_no,line in enumerate(text.splitlines(),1):
        for ordinal,sentence in enumerate(split_sentences(line),1):
            if concept not in sentence:continue
            if len(out)>=limit:break
            hedges=[term for term in UNCERTAINTY if term in sentence]
            out.append({
                "id":hashlib.sha256(f"{line_no}:{ordinal}:{sentence}".encode("utf-8")).hexdigest()[:24],
                "concept":concept,"source":str(path),"line":line_no,
                "sentence_index":ordinal,"excerpt":sentence,
                "source_truth_state":"UNVERIFIED",
                "review_status":"PENDING_HUMAN_REVIEW",
                "speculative":bool(hedges),"uncertainty_markers":hedges,
                "auto_promoted":False,
            })
        if len(out)>=limit:break
    return out

def review(source,concept,limit=30):
    path=Path(source)
    items=collect(path,concept,limit)
    return {"version":"v0.3.7.0","concept":concept,"source":str(path),
            "matching_excerpts":len(items),"authoritative_propositions_added":0,
            "truth_gate_modified":False,"checkpoint_modified":False,
            "review_candidates":items}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("concept")
    p.add_argument("--corpus",default="data/data-nagato.txt")
    p.add_argument("--limit",type=int,default=30)
    p.add_argument("--report",default=None)
    args=p.parse_args()
    result=review(args.corpus,args.concept,args.limit)
    data=json.dumps(result,ensure_ascii=False,indent=2)
    print(data)
    if args.report:
        target=Path(args.report);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(data,encoding="utf-8")
        print("report:",target)
    return 0

if __name__=="__main__":raise SystemExit(main())
