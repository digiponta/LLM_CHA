"""v0.13.13 explicit, reversible pilot promotion.

Requires --promote and passing v0.13.12 report. Copies candidate checkpoint,
merges fingerprint state (never removes trained IDs), and backs up originals.
Does not change approval/truth state or knowledge ledgers.
"""
import argparse
import json
import shutil
from pathlib import Path
from promote_unapproved_candidate_v01312 import assess

def merge_states(production, pilot):
    def ids(path):
        if not path.exists():return set()
        obj=json.loads(path.read_text(encoding="utf-8-sig"))
        return set(obj.get("trained_fingerprints",[]))
    combined=ids(production)|ids(pilot)
    return {"version":"v0.13.13","trained_fingerprints":sorted(combined)}

def promote(base,candidate,production_state,pilot_state,report_path):
    report=json.loads(report_path.read_text(encoding="utf-8-sig"))
    reasons=assess(report,base,candidate,pilot_state)
    if reasons:raise ValueError("; ".join(reasons))
    if base.resolve()==candidate.resolve() or production_state.resolve()==pilot_state.resolve():
        raise ValueError("production and candidate paths must differ")
    backup_model=base.with_name(base.name+".pre-v01313.bak")
    backup_state=production_state.with_name(production_state.name+".pre-v01313.bak")
    for backup in (backup_model,backup_state):
        if backup.exists():raise FileExistsError(f"backup exists, refusing overwrite: {backup}")
    combined=merge_states(production_state,pilot_state)
    base.parent.mkdir(parents=True,exist_ok=True)
    production_state.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(base,backup_model)
    if production_state.exists():
        shutil.copy2(production_state,backup_state)
    else:
        backup_state.write_text('{"trained_fingerprints":[]}\n',encoding="utf-8")
    try:
        temp_model=base.with_name(base.name+".v01313.tmp")
        temp_state=production_state.with_name(production_state.name+".v01313.tmp")
        shutil.copy2(candidate,temp_model)
        temp_state.write_text(json.dumps(combined,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        temp_model.replace(base)
        temp_state.replace(production_state)
    except Exception:
        shutil.copy2(backup_model,base)
        shutil.copy2(backup_state,production_state)
        raise
    return {"status":"PROMOTED","backup_model":str(backup_model),
            "backup_state":str(backup_state),"merged_fingerprints":len(combined["trained_fingerprints"]),
            "approval_status_modified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,default=Path("results/unapproved_checkpoint_comparison_v01311.json"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--candidate",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-pilot-v01310.pt"))
    p.add_argument("--production-state",type=Path,default=Path("data/chat_learning_state.json"))
    p.add_argument("--pilot-state",type=Path,default=Path("results/unapproved_pilot_state_v01310.json"))
    p.add_argument("--promote",action="store_true")
    args=p.parse_args()
    report=json.loads(args.report.read_text(encoding="utf-8-sig"))
    reasons=assess(report,args.base,args.candidate,args.pilot_state)
    if not args.promote:
        print(json.dumps({"status":"PREFLIGHT_PASS" if not reasons else "BLOCKED",
                          "reasons":reasons,"promotion_executed":False},ensure_ascii=False,indent=2))
        return
    if reasons:p.error("; ".join(reasons))
    result=promote(args.base,args.candidate,args.production_state,args.pilot_state,args.report)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
