#!/usr/bin/env python3
"""LLM_CHA v0.4.28.53: context ablation preparation and AI review diagnostics.

No model inference is performed. Structural context availability is not model accuracy.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.53"
FIELDS = ("relevance","semantic_consistency","context_independence","factual_correctness","training_suitability")
TURN = re.compile(r"(?m)^(人|相手):\s*(.*)$")

def variants(question):
    matches = list(TURN.finditer(question))
    if not matches:
        return {"history": question, "last_user": question, "history_turns": 0, "format_valid": False}
    # Strictly require complete line-by-line alternating speaker labels.
    lines = [x.strip() for x in question.splitlines() if x.strip()]
    parsed = [TURN.fullmatch(x) for x in lines]
    ok = all(parsed) and all(m.group(2).strip() for m in parsed)
    if ok:
        roles = [m.group(1) for m in parsed]
        ok = roles[-1] == "人" and all(a != b for a,b in zip(roles,roles[1:]))
    if not ok:
        return {"history": question, "last_user": None, "history_turns": 0, "format_valid": False}
    return {"history": question, "last_user": parsed[-1].group(2).strip(),
            "history_turns": len(parsed)-1, "format_valid": True}

def report(data):
    if data.get("version") != "v0.4.28.52" or data.get("mode") != "AI_ASSISTED_QA_REVIEW":
        raise ValueError("expected v0.4.28.52 AI review")
    rows = data.get("records")
    if not isinstance(rows,list) or len(rows) != data.get("sample_size") or not rows:
        raise ValueError("sample size mismatch")
    if data.get("train_ready") is not False or data.get("human_verified") is not False:
        raise ValueError("unsafe approval status")
    ids=set()
    counts={f:Counter() for f in FIELDS}
    output=[]
    for row in rows:
        rid=row.get("id")
        if not isinstance(rid,str) or not rid or rid in ids:
            raise ValueError("missing/duplicate ID")
        ids.add(rid)
        if row.get("review_status") != "ai_reviewed" or row.get("train_eligible") is not False:
            raise ValueError("unsafe record")
        ratings=row.get("ratings")
        if not isinstance(ratings,dict) or set(ratings)!=set(FIELDS):
            raise ValueError("invalid ratings")
        for field in FIELDS:
            if ratings[field] not in ("pass","fail","unknown"):
                raise ValueError("invalid rating value")
            counts[field][ratings[field]]+=1
        q=row.get("question")
        a=row.get("answer")
        if not isinstance(q,str) or not isinstance(a,str) or not q.strip() or not a.strip():
            raise ValueError("invalid QA text")
        v=variants(q)
        output.append({"id":rid,"source_split":row.get("source_split"),
                       "source_line":row.get("source_line"),
                       "full_context":q,"last_user_only":v["last_user"],
                       "target_response":a,"context_turns":v["history_turns"],
                       "context_format_valid":v["format_valid"],
                       "review_ratings":ratings,
                       "review_status":"ai_reviewed","train_eligible":False})
    contexts=sum(r["context_format_valid"] for r in output)
    return {"version":VERSION,"mode":"CONTEXT_ABLATION_PREPARATION",
            "sample_size":len(output),
            "context_format_valid":contexts,
            "context_format_invalid":len(output)-contexts,
            "review_counts":{k:dict(v) for k,v in counts.items()},
            "training_suitability_fail_ids":[r["id"] for r in output if r["review_ratings"]["training_suitability"]=="fail"],
            "duplicate_ids_in_sample":0,
            "ablations":{"full_context":{"inference_run":False,"accuracy":None},
                         "last_user_only":{"inference_run":False,"accuracy":None}},
            "examples":output,"accepted":0,"human_verified":False,
            "train_ready":False,"evaluation_ready":False,"runtime_modified":False,
            "notes":["This exports matched inputs for future model A/B testing; no generation or accuracy metrics.",
                     "AI judgments are provisional, not human ground truth.",
                     "Train/val/test leakage cannot be determined from a train-only sample.",
                     "Run cross-split overlap checks on original complete split files separately."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review",required=True)
    p.add_argument("--output",default="results/rpc_context_ablation_v042853.json")
    args=p.parse_args()
    result=report(json.loads(Path(args.review).read_text(encoding="utf-8")))
    dest=Path(args.output)
    if dest.resolve()==Path(args.review).resolve():
        raise ValueError("cannot overwrite review input")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("version","sample_size","context_format_valid","context_format_invalid","review_counts","training_suitability_fail_ids","train_ready")},ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
