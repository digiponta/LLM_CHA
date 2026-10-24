"""v0.7.44.50: idempotent backfill of unapproved Semantic candidates."""
import argparse
import json
from pathlib import Path
from unapproved_llm_intake_v074446 import DEFAULT_STORE, _read, _save
from unapproved_semantic_structure_v074449 import extract_structure

def backfill(path=DEFAULT_STORE, dry_run=False):
    p=Path(path)
    data=_read(p)
    stats={"total":len(data["candidates"]),"added":0,"preserved":0,
           "structured":0,"unstructured":0,"dry_run":bool(dry_run)}
    for row in data["candidates"]:
        if "semantic_candidate" in row:
            stats["preserved"]+=1
            continue
        result=extract_structure(row.get("natural_language",""),row.get("subject",""))
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
    args=parser.parse_args()
    print(json.dumps(backfill(args.store,args.dry_run),ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
