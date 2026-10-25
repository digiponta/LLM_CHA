"""Web pending excerpts -> review-only sentence candidates.

No network calls, truth assertions, model training, or auto-promotion.
Only conservative sentence-shaped quotations are extracted, NOT parsed facts.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

IN_SCHEMA="web_pending_v097"
OUT_SCHEMA="web_semantic_candidate_v0972"

def sentence_candidates(record, minimum=24, maximum=450):
    if record.get("schema") != IN_SCHEMA or record.get("state") != "PENDING_REVIEW":
        raise ValueError("Input must be a pending Web acquisition record")
    if record.get("train_ready") is not False or record.get("auto_promote") is not False:
        raise ValueError("Unexpected training/promotion state")
    source=record.get("url")
    excerpt=record.get("excerpt")
    if not isinstance(source,str) or not source.startswith(("https://","http://")):
        raise ValueError("Missing provenance URL")
    if not isinstance(excerpt,str):
        raise ValueError("Missing source excerpt")
    # The boundaries are heuristic. No claim that fragments are propositions.
    chunks=re.split(r"(?<=[。！？!?])\s*|(?<=[.!?])\s+",excerpt)
    seen=set()
    results=[]
    for i,chunk in enumerate(chunks):
        quote=chunk.strip()
        if not minimum<=len(quote)<=maximum or quote in seen:
            continue
        seen.add(quote)
        digest=hashlib.sha256((source+"\n"+quote).encode("utf-8")).hexdigest()
        results.append({
            "schema":OUT_SCHEMA,"candidate_id":digest[:24],
            "text":quote,"candidate_kind":"UNVERIFIED_SOURCE_QUOTE",
            "source_url":source,"source_title":record.get("title",""),
            "source_retrieved_at":record.get("retrieved_at"),
            "source_schema":IN_SCHEMA,"source_sentence_index":i,
            "source_hash":hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
            "state":"PENDING_REVIEW","truth_state":"EXTERNAL_UNVERIFIED",
            "rights_state":"UNKNOWN","train_ready":False,"auto_promote":False,
            "semantic_memory_approved":False,
            "review_required":["source_reliability","rights","factuality",
                               "sentence_boundary","prompt_injection"]})
    return results

def process(input_path, output_path):
    source=Path(input_path)
    dest=Path(output_path)
    if source.resolve()==dest.resolve():
        raise ValueError("Input/output must differ")
    if not source.exists():
        raise FileNotFoundError(str(source))
    # Parse and validate all records before opening the destination.
    pending=[]
    for n,line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():
            continue
        try:
            pending.extend(sentence_candidates(json.loads(line)))
        except (ValueError,TypeError,KeyError) as exc:
            raise ValueError(f"line {n}: {exc}") from exc
    unique={item["candidate_id"]:item for item in pending}
    items=list(unique.values())
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("w",encoding="utf-8") as file:
        for item in items:
            file.write(json.dumps(item,ensure_ascii=False)+"\n")
    return {"status":"REVIEW_CANDIDATES_CREATED","input_records":len(
        [line for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]),
        "candidate_count":len(items),"output":str(dest),
        "train_ready":False,"auto_promote":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",nargs="?",default="data/web_pending_v097.jsonl")
    parser.add_argument("output",nargs="?",default="data/web_semantic_candidates_v0972.jsonl")
    args=parser.parse_args()
    print(json.dumps(process(args.source,args.output),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
