#!/usr/bin/env python3
"""LLM_CHA v0.4.28.59: incremental, auditable conversation semantic state.

Propositions are unverified user reports. Opposite polarity is a possible
change/contradiction, NOT proof of either. Atomic persistence, no LLM training.
"""
import argparse
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from semantic_extraction_v042858 import build_from_turns, apply_turn

VERSION="v0.4.28.59"

def canonical_key(p):
    return (p["subject"],p["predicate"],p["object"],bool(p["polarity"]))

def reindex(memory):
    """Derive summary from immutable evidence list; preserve all source turns."""
    propositions=memory.get("propositions",[])
    grouped={}
    for p in propositions:
        if p.get("status")!="candidate" or p.get("truth_state")!="USER_REPORTED_UNVERIFIED":
            raise ValueError("cannot index unsupported proposition")
        grouped.setdefault(canonical_key(p),[]).append(p["source_turn"])
    index=[]
    for key,turns in sorted(grouped.items(),key=lambda it:(it[0][0],it[0][1],it[0][2],it[0][3])):
        subject,predicate,obj,polarity=key
        index.append({"subject":subject,"predicate":predicate,"object":obj,
                      "polarity":polarity,"source_turns":sorted(set(turns)),
                      "occurrences":len(turns),"truth_state":"USER_REPORTED_UNVERIFIED"})
    contradictory=[]
    by_object={}
    for entry in index:
        base=(entry["subject"],entry["predicate"],entry["object"])
        by_object.setdefault(base,[]).append(entry)
    for key,entries in by_object.items():
        if len({e["polarity"] for e in entries})>1:
            contradictory.append({"subject":key[0],"predicate":key[1],"object":key[2],
                                  "kind":"POSSIBLE_STATE_CHANGE_OR_CONTRADICTION",
                                  "source_turns":sorted({t for e in entries for t in e["source_turns"]}),
                                  "resolved":False})
    memory["proposition_index"]=index
    memory["conflict_candidates"]=contradictory
    memory["index_version"]=VERSION
    memory["train_ready"]=False
    return memory

def append(memory,role,text,*,turn_id=None,recent_limit=5):
    staged=deepcopy(memory)
    previous=staged.get("current_topic")
    apply_turn(staged,role,text,turn_id=turn_id,recent_limit=recent_limit)
    current=staged.get("current_topic")
    events=staged.setdefault("topic_transitions",[])
    if current is not None and current!=previous:
        events.append({"turn_id":staged["last_turn"],"from":previous,"to":current})
    reindex(staged)
    staged["incremental_version"]=VERSION
    # Commit only when all operations succeed.
    memory.clear()
    memory.update(staged)
    return memory

def validate(memory):
    if memory.get("train_ready") is not False or memory.get("promotion_status")!="not_promoted":
        raise ValueError("unsafe persisted memory state")
    if not isinstance(memory.get("conversation_id"),str) or not memory["conversation_id"]:
        raise ValueError("missing conversation ID")
    turns=memory.get("last_turn")
    if not isinstance(turns,int) or isinstance(turns,bool) or turns<0:
        raise ValueError("invalid last turn")
    for p in memory.get("propositions",[]):
        source=p.get("source_turn")
        if not isinstance(source,int) or source<1 or source>turns:
            raise ValueError("invalid proposition provenance")
    expected=deepcopy(memory)
    reindex(expected)
    for field in ("proposition_index","conflict_candidates"):
        if field in memory and memory[field]!=expected[field]:
            raise ValueError(f"inconsistent {field}")
    return expected

def save_atomic(memory,path):
    validated=validate(memory)
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=".csm-",suffix=".tmp",dir=str(target.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(validated,stream,ensure_ascii=False,indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp,target)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def load(path):
    memory=json.loads(Path(path).read_text(encoding="utf-8"))
    return validate(memory)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True,help="JSON with conversation_id and turns")
    p.add_argument("--state",required=True,help="Persistent memory JSON path")
    p.add_argument("--recent-limit",type=int,default=5)
    a=p.parse_args()
    data=json.loads(Path(a.input).read_text(encoding="utf-8"))
    state_path=Path(a.state)
    if state_path.resolve()==Path(a.input).resolve():
        raise ValueError("input and state paths must differ")
    if state_path.exists():
        memory=load(state_path)
        if memory["conversation_id"]!=data["conversation_id"]:
            raise ValueError("conversation ID mismatch")
    else:
        from conversation_semantic_memory_v042857 import new_memory
        memory=new_memory(data["conversation_id"])
    for turn in data["turns"]:
        append(memory,turn["role"],turn["text"],
               turn_id=turn.get("turn_id"),recent_limit=a.recent_limit)
    save_atomic(memory,state_path)
    print(json.dumps({"version":VERSION,"conversation_id":memory["conversation_id"],
        "last_turn":memory["last_turn"],"unique_propositions":len(memory["proposition_index"]),
        "conflicts":len(memory["conflict_candidates"]),
        "topic_transitions":len(memory.get("topic_transitions",[])),
        "train_ready":False,"runtime_modified":False},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
