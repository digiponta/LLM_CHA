"""v0.7.44.50: idempotent backfill of unapproved Semantic candidates."""
import argparse
import json
from pathlib import Path
from unapproved_llm_intake_v074446 import DEFAULT_STORE, _read, _save
from unapproved_semantic_structure_v074449 import extract_structure

def backfill(path=DEFAULT_STORE, dry_run=False, recheck_unstructured=False):
    p=Path(path)
    data=_read(p)
    stats={"total":len(data["candidates"]),"added":0,"preserved":0,
           "structured":0,"unstructured":0,"dry_run":bool(dry_run)}
    stats["rechecked"]=0
    stats["reasons"]={}
    for row in data["candidates"]:
        previous=row.get("semantic_candidate")
        if previous is not None and not (recheck_unstructured and previous.get("status")=="UNSTRUCTURED"):
            stats["preserved"]+=1
            continue
        if previous is not None: stats["rechecked"]+=1
        result=extract_structure(row.get("natural_language",""),row.get("subject",""))
        if result["status"]=="UNSTRUCTURED":
            reason=result.get("reason","UNKNOWN")
            stats["reasons"][reason]=stats["reasons"].get(reason,0)+1
        if result["status"]=="STRUCTURED":
            stats["structured"]+=1
        else:
            stats["unstructured"]+=1
        stats["added"]+=1
        if not dry_run:
            row["semantic_candidate"]=result
    if stats["added"] and not dry_run:
        _save(p,data)
    return stats

def main():
    parser=argparse.ArgumentParser(description="Backfill isolated unapproved Semantic structure")
    parser.add_argument("--store",default=str(DEFAULT_STORE))
    parser.add_argument("--dry-run",action="store_true")
    parser.add_argument("--recheck-unstructured",action="store_true")
    args=parser.parse_args()
    print(json.dumps(backfill(args.store,args.dry_run,args.recheck_unstructured),ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
