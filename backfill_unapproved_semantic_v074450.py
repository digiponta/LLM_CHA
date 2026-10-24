"""v0.7.44.52: versioned, idempotent Semantic candidate backfill."""
import argparse
import json
from pathlib import Path
from unapproved_llm_intake_v074446 import DEFAULT_STORE, _read, _save
from unapproved_semantic_structure_v074449 import EXTRACTOR_VERSION, extract_structure

def backfill(path=DEFAULT_STORE, dry_run=False, recheck_unstructured=False, force=False):
    data=_read(path)
    stats={"total":len(data["candidates"]),"added":0,"preserved":0,
           "structured":0,"unstructured":0,"dry_run":bool(dry_run),
           "rechecked":0,"changed":0,"reasons":{},"extractor_version":EXTRACTOR_VERSION}
    write=False
    for row in data["candidates"]:
        previous=row.get("semantic_candidate")
        previous_version=(previous or {}).get("extractor_version")
        if previous is not None and not force:
            if not (recheck_unstructured and previous.get("status")=="UNSTRUCTURED"
                    and previous_version != EXTRACTOR_VERSION):
                stats["preserved"]+=1
                continue
        if previous is not None:
            stats["rechecked"]+=1
        new=extract_structure(row.get("natural_language",""),row.get("subject",""))
        new["extractor_version"]=EXTRACTOR_VERSION
        stats["added"]+=1
        stats["structured" if new["status"]=="STRUCTURED" else "unstructured"]+=1
        if new["status"]=="UNSTRUCTURED":
            reason=new.get("reason","UNKNOWN")
            stats["reasons"][reason]=stats["reasons"].get(reason,0)+1
        if previous != new:
            stats["changed"]+=1
            if not dry_run:
                row["semantic_candidate"]=new
                write=True
    if write and not dry_run:
        _save(path,data)
    return stats

def main():
    parser=argparse.ArgumentParser(description="Version-aware unapproved Semantic backfill")
    parser.add_argument("--store",default=str(DEFAULT_STORE))
    parser.add_argument("--dry-run",action="store_true")
    parser.add_argument("--recheck-unstructured",action="store_true")
    parser.add_argument("--force",action="store_true",help="Explicitly recompute even already-versioned results")
    args=parser.parse_args()
    print(json.dumps(backfill(args.store,args.dry_run,args.recheck_unstructured,args.force),ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
