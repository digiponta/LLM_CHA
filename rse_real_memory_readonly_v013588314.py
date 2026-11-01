"""Read-only real-store bridge, fail closed on missing explicit approval/truth.

No chat.py modifications, no bootstrapping, no store writes or live response.
The source schema is checked explicitly: approval and truth are distinct.
"""
import argparse,json
from pathlib import Path
from rse_memory_theme_shadow_v013588313 import decide

DEFAULT_UNIFIED="data/unified_semantic_memory_v1090.jsonl"
DEFAULT_TRUTH="data/truth_state_v10103.jsonl"

def jsonl(path):
    p=Path(path)
    if not p.is_file():return []
    result=[]
    for lineno,line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():continue
        try: row=json.loads(line)
        except ValueError as exc:raise ValueError(f"{p}:{lineno}: invalid json") from exc
        if not isinstance(row,dict):raise ValueError(f"{p}:{lineno}: expected object")
        result.append(row)
    return result

def adapt(unified_path,truth_path):
    unified=jsonl(unified_path)
    truth={}
    for row in jsonl(truth_path):
        concept=str(row.get("concept","")).strip()
        if concept:truth[concept]=str(row.get("state","UNVERIFIED")).upper()
    records=[]
    for index,row in enumerate(unified):
        concept=str(row.get("concept","")).strip()
        answer=str(row.get("assistant","")).strip()
        if not concept or not answer:continue
        # Never equate 'present in unified memory' with user approval.
        explicit_approval=row.get("approved") is True or row.get("approval_state")=="APPROVED"
        verified=truth.get(concept)=="TRUE" and explicit_approval
        records.append({
            "id":f"unified:{index}","query":f"{concept}とは",
            "answer":answer,"approved":explicit_approval,"verified":verified
        })
    return records,{"unified_rows":len(unified),"truth_rows":len(truth),
                    "adapted_records":len(records),
                    "explicitly_approved_and_true":sum(x["approved"] and x["verified"] for x in records)}

def run(query,unified_path,truth_path,candidates):
    records,stats=adapt(unified_path,truth_path)
    result=decide(query,records,candidates)
    # Avoid unverified memory text in audit output.
    result["store_statistics"]=stats
    result["read_only"]=True
    result["real_store_adapter"]=True
    result["live_integration"]=False
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",required=True)
    p.add_argument("--unified",default=DEFAULT_UNIFIED)
    p.add_argument("--truth",default=DEFAULT_TRUTH)
    p.add_argument("--candidates",default="data/rse_theme_examples_v013588312.json")
    a=p.parse_args()
    data=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))
    result=run(a.query,a.unified,a.truth,data["candidates"])
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
