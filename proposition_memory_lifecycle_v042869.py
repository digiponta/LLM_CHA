#!/usr/bin/env python3
"""LLM_CHA v0.4.28.69: reviewable proposition candidate lifecycle.

Import v0.4.28.68 artifact. VERIFIED means explicitly reviewed as an
accurate *speaker report*, not that a real-world proposition is true.
No automatic Fact Memory promotion, model learning, or runtime changes.
"""
import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from conversation_resource_memory_v042866 import write_json_atomic

VERSION="v0.4.28.69"
STATES=("CANDIDATE","REVIEW_REQUIRED","VERIFIED","REJECTED","SUPERSEDED")
ACTIONS={"review":"REVIEW_REQUIRED","verify":"VERIFIED",
         "reject":"REJECTED","supersede":"SUPERSEDED"}

def _digest(value):
    blob=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def import_candidates(artifact):
    if artifact.get("category")!="PROPOSITION_CANDIDATES" or artifact.get("train_ready") is not False or artifact.get("fact_promoted") is not False:
        raise ValueError("unsafe source artifact")
    cid=artifact.get("conversation_id")
    fp=artifact.get("source_fingerprint")
    if not isinstance(cid,str) or not cid or not isinstance(fp,str) or len(fp)!=64:
        raise ValueError("invalid source identity")
    items=[]
    ids=set()
    for p in artifact.get("candidates",[]):
        if p.get("conversation_id")!=cid or p.get("speaker") not in ("A","B") or p.get("subject")!=p["speaker"] or p.get("truth_state")!="SPEAKER_REPORTED_UNVERIFIED":
            raise ValueError("invalid proposition source")
        if type(p.get("source_turn")) is not int or not 1<=p["source_turn"]<=artifact["source_turns"]:
            raise ValueError("invalid source turn")
        pid=_digest({"source":fp,"proposition":p})
        if pid in ids:raise ValueError("duplicate proposition")
        ids.add(pid)
        items.append({"id":pid,"claim":deepcopy(p),"state":"CANDIDATE",
             "review_events":[],"reviewed_report":False,"fact_verified":False})
    return {"version":VERSION,"category":"PROPOSITION_MEMORY",
        "conversation_id":cid,"source_fingerprint":fp,
        "source_turns":artifact["source_turns"],"source_artifact_sha256":_digest(artifact),
        "items":items,"train_ready":False,"fact_promoted":False}

def validate(memory):
    if memory.get("category")!="PROPOSITION_MEMORY" or memory.get("train_ready") is not False or memory.get("fact_promoted") is not False:
        raise ValueError("invalid proposition memory")
    if not isinstance(memory.get("items"),list):raise ValueError("missing items")
    ids=set()
    for item in memory["items"]:
        if item["id"] in ids or item["state"] not in STATES:raise ValueError("duplicate or invalid state")
        ids.add(item["id"])
        if item.get("fact_verified") is not False:raise ValueError("fact verification not supported")
        if item.get("reviewed_report") is not (item["state"]=="VERIFIED"):
            raise ValueError("review state mismatch")
    return memory

def transition(memory,item_id,action,*,reviewer,reason,evidence_reference=None):
    validate(memory)
    if action not in ACTIONS:raise ValueError("invalid transition action")
    if not isinstance(reviewer,str) or not reviewer.strip() or not isinstance(reason,str) or not reason.strip():
        raise ValueError("explicit reviewer and reason required")
    staged=deepcopy(memory)
    matches=[i for i in staged["items"] if i["id"]==item_id]
    if len(matches)!=1:raise ValueError("unknown item ID")
    item=matches[0]
    state=item["state"];next_state=ACTIONS[action]
    allowed={"CANDIDATE":{"review","reject"},
             "REVIEW_REQUIRED":{"verify","reject","supersede"},
             "VERIFIED":{"supersede"},
             "REJECTED":set(),"SUPERSEDED":set()}
    if action not in allowed[state]:raise ValueError("disallowed state transition")
    if action=="verify" and not isinstance(evidence_reference,str):
        raise ValueError("verify requires independent review evidence reference")
    if action=="verify" and not evidence_reference.strip():
        raise ValueError("empty evidence reference")
    item["state"]=next_state
    item["reviewed_report"]=(next_state=="VERIFIED")
    item["review_events"].append({"from":state,"to":next_state,
        "reviewer":reviewer.strip(),"reason":reason.strip(),
        "evidence_reference":evidence_reference})
    validate(staged)
    memory.clear();memory.update(staged)
    return item

def run_import(source_path,output_path):
    source=Path(source_path);output=Path(output_path)
    if source.resolve()==output.resolve():raise ValueError("source and output must differ")
    artifact=json.loads(source.read_text(encoding="utf-8-sig"))
    new=import_candidates(artifact)
    if output.exists():
        existing=json.loads(output.read_text(encoding="utf-8-sig"))
        validate(existing)
        if (existing["source_artifact_sha256"]!=new["source_artifact_sha256"]
            or [i["id"] for i in existing["items"]]!=[i["id"] for i in new["items"]]):
            raise ValueError("source differs from existing reviewed memory")
        return existing
    write_json_atomic(new,output)
    return new

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    m=run_import(a.candidates,a.output)
    print(json.dumps({"version":VERSION,"conversation_id":m["conversation_id"],
     "items":len(m["items"]),"states":{s:sum(i["state"]==s for i in m["items"]) for s in STATES},
     "train_ready":False,"fact_promoted":False},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
