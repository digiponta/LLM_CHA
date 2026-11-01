"""Propose (never automatically apply) Unified Memory repairs from atomic truth source."""
import argparse,json
from pathlib import Path
from semantic_proposition_v1090 import compose_propositions,load_propositions
from rse_real_memory_readonly_v013588314 import jsonl

def propose(atomic_path,unified_path):
    atoms=load_propositions(Path(atomic_path))
    rows=jsonl(unified_path)
    changes=[]
    for i,row in enumerate(rows):
        subject=str(row.get("concept","")).strip()
        answer=str(row.get("assistant","")).strip()
        if not subject or not answer or "であるである" not in answer:continue
        related=[p for p in atoms if p.subject==subject]
        if not related:continue
        expected=compose_propositions(related,subject)
        if expected==answer or not expected:continue
        # Only exact, atomic-backed regeneration, never freeform string replacement.
        changes.append({"row_index":i,"concept":subject,"before":answer,
                        "proposed":expected,"source":"atomic-proposition",
                        "requires_manual_approval":True})
    return {"status":"DRY_RUN_ONLY","total_unified_rows":len(rows),
            "proposed_repairs":len(changes),"changes":changes,
            "source_files_modified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--atomic",default="data/semantic_propositions_v1090.jsonl")
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--report",default="results/rse_unified_repair_proposal_v013588317.json")
    args=p.parse_args()
    result=propose(args.atomic,args.unified)
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
