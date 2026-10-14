#!/usr/bin/env python3
"""LLM_CHA v0.4.28.68 - local /sleep candidate extraction transaction.

Writes a separate proposition candidate artifact before marking CONVERSATION
SLEEP_COMPLETED. Candidates are unverified; no Fact Memory promotion.
Recovery: if artifact exists but checkpoint was not updated, verify artifact
against the current conversation and finish the checkpoint.
"""
import argparse
import hashlib
import json
from pathlib import Path
from conversation_resource_memory_v042866 import validate,write_json_atomic,sleep_checkpoint
from diagnose_jdd_candidate_expansion_v042865 import expanded_candidates

VERSION="v0.4.28.68"

def fingerprint(memory):
    canonical=json.dumps({"conversation_id":memory["conversation_id"],
      "turns":memory["turns"]},ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def extract(memory):
    validate(memory)
    cid=memory["conversation_id"]
    candidates=[];guard_counts={}
    for turn in memory["turns"]:
        speaker=turn["speaker"]
        if speaker not in ("A","B"):
            # Existing extractor is only validated for corpus speaker A/B.
            # Do not fabricate an identity mapping from user/assistant.
            raise ValueError("v0.4.28.68 only supports A/B conversation speakers")
        found,guards=expanded_candidates(cid,turn)
        candidates.extend(found)
        for g in guards:guard_counts[g]=guard_counts.get(g,0)+1
    return {"version":VERSION,"category":"PROPOSITION_CANDIDATES",
        "conversation_id":cid,"source_fingerprint":fingerprint(memory),
        "source_turns":memory["last_turn"],"candidates":candidates,
        "guard_counts":guard_counts,"truth_state":"UNVERIFIED",
        "human_verified":False,"train_ready":False,
        "fact_promoted":False,"runtime_modified":False}

def validate_artifact(artifact,expected):
    if artifact!=expected:
        raise ValueError("saved candidate artifact does not match source; refusing completion")

def run(conversation_path,candidate_path):
    source=Path(conversation_path)
    destination=Path(candidate_path)
    if source.resolve()==destination.resolve():
        raise ValueError("source and candidate files must differ")
    # File locking is NOT provided: run only as a single writer with no
    # concurrent conversation modification or eviction.
    memory=json.loads(source.read_text(encoding="utf-8-sig"))
    validate(memory)
    if memory["active"]:raise ValueError("active conversation cannot be finalized")
    if memory["status"]=="SLEEP_IN_PROGRESS":
        raise ValueError("in-progress external sleep session is not owned by this runner")
    candidate=extract(memory)
    if destination.exists():
        saved=json.loads(destination.read_text(encoding="utf-8-sig"))
        validate_artifact(saved,candidate)
        disposition="VERIFIED_EXISTING"
    else:
        write_json_atomic(candidate,destination)
        saved=json.loads(destination.read_text(encoding="utf-8-sig"))
        validate_artifact(saved,candidate)
        disposition="CREATED"
    if memory["status"]!="SLEEP_COMPLETED":
        sleep_checkpoint(memory,memory["last_turn"],completed=True)
        # Verify candidate artifact exists before marking source as completed.
        write_json_atomic(memory,source)
    return {"version":VERSION,"conversation_id":memory["conversation_id"],
        "status":memory["status"],"source_turns":memory["last_turn"],
        "candidates":len(candidate["candidates"]),
        "candidate_artifact":str(destination),
        "candidate_status":disposition,"train_ready":False,
        "fact_promoted":False,"runtime_modified":False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conversation",required=True)
    ap.add_argument("--candidates",required=True)
    args=ap.parse_args()
    print(json.dumps(run(args.conversation,args.candidates),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
