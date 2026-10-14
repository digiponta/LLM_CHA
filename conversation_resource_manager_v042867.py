#!/usr/bin/env python3
"""LLM_CHA v0.4.28.67: safe disk budget planner for isolated conversation JSON.

Default dry-run. Destructive mode needs --apply and --confirm-delete.
Only *.conversation.json files directly inside --directory are considered.
No unlink of source files, symlinks, unknown categories, active/in-progress
records or unprocessed records. Persistent audit is mandatory before deletion.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from conversation_resource_memory_v042866 import validate, write_json_atomic

VERSION="v0.4.28.67"
SUFFIX=".conversation.json"

def inspect(directory):
    root=Path(directory).resolve(strict=True)
    if not root.is_dir():raise ValueError("not a directory")
    records=[];ids=set()
    for path in sorted(root.iterdir()):
        if not path.name.endswith(SUFFIX):continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("unsupported symlink or nonfile in conversation store")
        raw=path.read_bytes()
        data=json.loads(raw.decode("utf-8-sig"))
        validate(data)
        if data["conversation_id"] in ids:raise ValueError("duplicate conversation id")
        ids.add(data["conversation_id"])
        records.append({"path":path,"data":data,"size":len(raw),
                        "sha256":hashlib.sha256(raw).hexdigest()})
    return root,records

def plan(directory,budget_bytes):
    if type(budget_bytes) is not int or budget_bytes<0:raise ValueError("invalid budget")
    root,records=inspect(directory)
    before=sum(x["size"] for x in records)
    remaining=before;chosen=[]
    eligible=[x for x in records if (
        not x["data"]["active"] and x["data"]["status"]=="SLEEP_COMPLETED"
        and x["data"]["sleep"]["completed"]
        and x["data"]["sleep"]["processed_turn"]==x["data"]["last_turn"]
        and x["data"]["resource_policy"]["evictable"]
    )]
    # deterministic: processed completed sessions, then lexicographic name
    for item in sorted(eligible,key=lambda x:x["path"].name):
        if remaining<=budget_bytes:break
        chosen.append({"filename":item["path"].name,
                      "conversation_id":item["data"]["conversation_id"],
                      "size_bytes":item["size"],"sha256":item["sha256"]})
        remaining-=item["size"]
    return {"version":VERSION,"directory":str(root),
            "budget_bytes":budget_bytes,"bytes_before":before,
            "bytes_after_estimate":remaining,"bytes_planned_to_free":before-remaining,
            "budget_satisfied_estimate":remaining<=budget_bytes,
            "candidate_files":chosen,"inspected_files":len(records),
            "unprocessed_loss_permitted":False}

def apply_plan(report,audit_path):
    root=Path(report["directory"]).resolve(strict=True)
    audit=Path(audit_path).resolve()
    if audit.parent==root or root in audit.parents:
        raise ValueError("audit must be outside conversation store")
    # Before any unlink, ensure the plan still matches on-disk files.
    fresh=plan(root,report["budget_bytes"])
    if fresh!=report:raise ValueError("store changed since plan; refuse")
    write_json_atomic({"phase":"PRE_DELETE","plan":report},audit)
    removed=[]
    for candidate in report["candidate_files"]:
        path=root/candidate["filename"]
        if path.is_symlink() or not path.is_file():
            raise ValueError("unexpected candidate file type")
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=candidate["sha256"]:
            raise ValueError("candidate mutated; abort")
        current=json.loads(raw.decode("utf-8-sig"))
        validate(current)
        if current["status"]!="SLEEP_COMPLETED" or current["active"]:
            raise ValueError("candidate no longer safe")
        path.unlink()
        removed.append(candidate["filename"])
    actual=sum(p.stat().st_size for p in root.iterdir()
               if p.name.endswith(SUFFIX) and p.is_file())
    result={"version":VERSION,"phase":"COMPLETED","removed":removed,
            "bytes_after_actual":actual,"budget_satisfied_actual":actual<=report["budget_bytes"]}
    write_json_atomic({"plan":report,"result":result},audit)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",required=True,help="Isolated conversation JSON directory")
    p.add_argument("--budget-bytes",required=True,type=int)
    p.add_argument("--audit",default="results/conversation_eviction_audit_v042867.json")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm-delete",action="store_true")
    a=p.parse_args()
    if a.confirm_delete and not a.apply:
        p.error("--confirm-delete requires --apply")
    report=plan(a.directory,a.budget_bytes)
    print(json.dumps({"mode":"APPLY" if a.apply else "DRY_RUN",**report},ensure_ascii=False,indent=2))
    if a.apply:
        if not a.confirm_delete:p.error("destructive operation needs --apply --confirm-delete")
        print(json.dumps(apply_plan(report,a.audit),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
