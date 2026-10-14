#!/usr/bin/env python3
"""LLM_CHA v0.4.28.66: evictable CONVERSATION memory.

Separate ephemeral conversation records from proposition and fact memory.
No extraction, verification, /sleep execution, or model training here.
"""
import argparse
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

VERSION="v0.4.28.66"
CATEGORY="CONVERSATION"
STATES=("PENDING_SLEEP","SLEEP_IN_PROGRESS","SLEEP_COMPLETED","SLEEP_FAILED")

def new_conversation(conversation_id):
    if not isinstance(conversation_id,str) or not conversation_id.strip():
        raise ValueError("nonempty conversation_id required")
    return {"version":VERSION,"category":CATEGORY,"conversation_id":conversation_id,
      "status":"PENDING_SLEEP","active":True,"last_turn":0,
      "turns":[],"semantic_context":{"keywords":[],"topics":[],"relations":[]},
      "sleep":{"processed_turn":0,"completed":False},
      "resource_policy":{"evictable":True,"protect_active_session":True,
          "prefer_processed":True},"train_ready":False}

def validate(memory):
    if not isinstance(memory,dict) or memory.get("category")!=CATEGORY:
        raise ValueError("not CONVERSATION memory")
    if memory.get("train_ready") is not False:
        raise ValueError("conversation cannot be train-ready")
    if not isinstance(memory.get("conversation_id"),str) or not memory["conversation_id"]:
        raise ValueError("invalid conversation ID")
    if memory.get("status") not in STATES or not isinstance(memory.get("active"),bool):
        raise ValueError("invalid lifecycle state")
    turns=memory.get("turns")
    if not isinstance(turns,list) or memory.get("last_turn")!=len(turns):
        raise ValueError("invalid turn list")
    for n,t in enumerate(turns,1):
        if not isinstance(t,dict) or t.get("turn_id")!=n or t.get("speaker") not in ("A","B","user","assistant") or not isinstance(t.get("text"),str) or not t["text"].strip():
            raise ValueError("invalid turn provenance")
    sp=memory.get("sleep")
    if not isinstance(sp,dict) or not isinstance(sp.get("processed_turn"),int) or not 0<=sp["processed_turn"]<=len(turns) or not isinstance(sp.get("completed"),bool):
        raise ValueError("invalid sleep checkpoint")
    if sp["completed"] != (memory["status"]=="SLEEP_COMPLETED"):
        raise ValueError("inconsistent sleep status")
    rp=memory.get("resource_policy")
    if not isinstance(rp,dict) or any(not isinstance(rp.get(k),bool) for k in ("evictable","protect_active_session","prefer_processed")):
        raise ValueError("invalid policy")
    return memory

def append_turn(memory,speaker,text,*,turn_id=None):
    validate(memory)
    if speaker not in ("A","B","user","assistant") or not isinstance(text,str) or not text.strip():
        raise ValueError("invalid speaker or text")
    staged=deepcopy(memory)
    if turn_id is None:turn_id=staged["last_turn"]+1
    if type(turn_id) is not int or turn_id!=staged["last_turn"]+1:
        raise ValueError("non-sequential turn")
    staged["turns"].append({"turn_id":turn_id,"speaker":speaker,"text":text.strip()})
    staged["last_turn"]=turn_id
    staged["status"]="PENDING_SLEEP"
    staged["sleep"]["completed"]=False
    validate(staged)
    memory.clear();memory.update(staged)
    return memory

def close_session(memory):
    validate(memory)
    memory["active"]=False
    return memory

def sleep_checkpoint(memory,processed_turn,*,completed=False):
    """Backend checkpoint only; does not assert successful extraction."""
    validate(memory)
    if type(processed_turn) is not int or not memory["sleep"]["processed_turn"]<=processed_turn<=memory["last_turn"]:
        raise ValueError("invalid sleep progress")
    if completed and processed_turn!=memory["last_turn"]:
        raise ValueError("cannot complete with unprocessed turns")
    staged=deepcopy(memory)
    staged["sleep"]["processed_turn"]=processed_turn
    staged["sleep"]["completed"]=completed
    staged["status"]="SLEEP_COMPLETED" if completed else "SLEEP_IN_PROGRESS"
    validate(staged)
    memory.clear();memory.update(staged)
    return memory

def size_bytes(memory):
    return len(json.dumps(memory,ensure_ascii=False,separators=(",",":")).encode("utf-8"))

def can_evict(memory,*,allow_unprocessed_loss=False):
    validate(memory)
    p=memory["resource_policy"]
    if not p["evictable"] or (memory["active"] and p["protect_active_session"]):
        return False
    if memory["status"]=="SLEEP_IN_PROGRESS":return False
    if not allow_unprocessed_loss and not memory["sleep"]["completed"]:return False
    return True

def evict_to_budget(records,budget_bytes,*,allow_unprocessed_loss=False):
    """Return survivors and audit (no filesystem deletion).

    Deterministic, processed-first, oldest-id ordering. Never edit originals.
    WARNING: with allow_unprocessed_loss=True, unprocessed talk may be lost.
    """
    if type(budget_bytes) is not int or budget_bytes<0:raise ValueError("invalid budget")
    if not isinstance(records,list):raise ValueError("records must be list")
    if len({r["conversation_id"] for r in records})!=len(records):
        raise ValueError("duplicate conversation IDs")
    for r in records:validate(r)
    original_size=sum(size_bytes(r) for r in records)
    survivors=list(records);removed=[]
    order=sorted(records,key=lambda r:(not r["sleep"]["completed"],r["conversation_id"]))
    for item in order:
        if sum(size_bytes(r) for r in survivors)<=budget_bytes:break
        if can_evict(item,allow_unprocessed_loss=allow_unprocessed_loss):
            survivors.remove(item)
            removed.append({"conversation_id":item["conversation_id"],
                "bytes_freed":size_bytes(item),
                "had_unprocessed_turns":not item["sleep"]["completed"]})
    after=sum(size_bytes(r) for r in survivors)
    return survivors,{"version":VERSION,"budget_bytes":budget_bytes,
      "bytes_before":original_size,"bytes_after":after,"bytes_freed":original_size-after,
      "budget_satisfied":after<=budget_bytes,"removed":removed,
      "unprocessed_loss_permitted":bool(allow_unprocessed_loss),
      "train_ready":False}

def write_json_atomic(data,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".conversation-",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.write("\n")
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,help="Local dialogue JSON with conversation_id and turns")
    p.add_argument("--output",default="results/conversation_resource_v042866.json")
    a=p.parse_args()
    src=Path(a.input);out=Path(a.output)
    if src.resolve()==out.resolve():raise ValueError("input/output must differ")
    d=json.loads(src.read_text(encoding="utf-8-sig"))
    m=new_conversation(d["conversation_id"])
    for t in d["turns"]:
        append_turn(m,t.get("speaker",t.get("role")),t["text"],turn_id=t.get("turn_id"))
    close_session(m)
    write_json_atomic(m,out)
    print(json.dumps({"version":VERSION,"category":CATEGORY,"turns":m["last_turn"],
     "bytes":size_bytes(m),"status":m["status"],"train_ready":False},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
