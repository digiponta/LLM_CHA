#!/usr/bin/env python3
"""LLM_CHA v0.4.28.70: evidence-gated /sleep -> Proposition -> eviction.

Default is dry-run, with no file deletion. Live deletion is intentionally
conservative: *every* turn must have a candidate, and an independent
speaker/turn/evidence excerpt must be committed before unlinking conversation.
No automatic fact verification/training. Single-writer only; no file locks.
"""
import argparse
import hashlib
import json
from pathlib import Path

from conversation_resource_memory_v042866 import validate,write_json_atomic
from conversation_sleep_backend_v042868 import run as sleep_run, fingerprint
from proposition_memory_lifecycle_v042869 import run_import,validate as validate_proposition

VERSION="v0.4.28.70"

def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,
       separators=(",",":")).encode("utf-8")).hexdigest()

def paths_safe(conversation,candidates,propositions,evidence,audit):
    resolved=[Path(p).resolve() for p in (conversation,candidates,propositions,evidence,audit)]
    if len(set(resolved))!=len(resolved):raise ValueError("all paths must be distinct")
    # Artifacts and audit must outlive removal of conversation file.
    for p in resolved[1:]:
        if p.parent==resolved[0].parent:
            raise ValueError("artifacts/audit must be outside conversation directory")
    return resolved

def evidence_record(memory,candidate_artifact):
    turns=memory["turns"]
    claims=candidate_artifact["candidates"]
    grouped={}
    for claim in claims:
        tid=claim["source_turn"]
        if not 1<=tid<=len(turns) or claim["speaker"]!=turns[tid-1]["speaker"]:
            raise ValueError("candidate provenance mismatch")
        grouped.setdefault(tid,[]).append(claim)
    # Deliberately do NOT treat unmatched utterances as processed evidence.
    uncovered=[t["turn_id"] for t in turns if t["turn_id"] not in grouped]
    entries=[{"source_turn":t["turn_id"],"speaker":t["speaker"],
       "source_text":t["text"],"source_sha256":hashlib.sha256(
          t["text"].encode("utf-8")).hexdigest(),
       "candidate_count":len(grouped.get(t["turn_id"],[]))}
       for t in turns if t["turn_id"] in grouped]
    return {"version":VERSION,"category":"SLEEP_EVIDENCE",
       "conversation_id":memory["conversation_id"],"source_fingerprint":fingerprint(memory),
       "source_turns":memory["last_turn"],"entries":entries,
       "uncovered_turns":uncovered,"train_ready":False,"fact_promoted":False}

def verify_bundle(memory,candidate,proposition,evidence):
    validate(memory);validate_proposition(proposition)
    if candidate.get("conversation_id")!=memory["conversation_id"]:
        raise ValueError("candidate session mismatch")
    if candidate.get("source_fingerprint")!=fingerprint(memory):
        raise ValueError("candidate source mismatch")
    if proposition.get("source_fingerprint")!=candidate.get("source_fingerprint"):
        raise ValueError("proposition source mismatch")
    if evidence != evidence_record(memory,candidate):
        raise ValueError("evidence mismatch")
    if len(proposition["items"])!=len(candidate["candidates"]):
        raise ValueError("candidate count mismatch")
    if evidence["uncovered_turns"]:
        return False,"UNCOVERED_TURNS"
    if not candidate["candidates"]:
        return False,"NO_CANDIDATES"
    if memory["active"] or memory["status"]!="SLEEP_COMPLETED":
        return False,"SLEEP_NOT_COMPLETED"
    return True,"EVIDENCE_PRESERVED"

def integrate(conversation,candidates,propositions,evidence,audit,*,apply=False,confirm_delete=False):
    src,cpath,ppath,epath,apath=paths_safe(
       conversation,candidates,propositions,evidence,audit)
    if confirm_delete and not apply:raise ValueError("confirm-delete requires apply")
    if apply and not confirm_delete:raise ValueError("deletion requires explicit confirmation")
    # Plan-only mode does not mutate the source or artifact files.
    if not apply:
        memory=json.loads(src.read_text(encoding="utf-8-sig"))
        validate(memory)
        from conversation_sleep_backend_v042868 import extract
        candidate=extract(memory)
        evid=evidence_record(memory,candidate)
        return {"version":VERSION,"mode":"DRY_RUN",
            "conversation_id":memory["conversation_id"],
            "candidate_count":len(candidate["candidates"]),
            "uncovered_turns":len(evid["uncovered_turns"]),
            "deletion_permitted":False,"reason":"DRY_RUN_NO_MUTATION"}
    # Idempotent recovery: if source was already removed, do not claim a
    # successful new deletion. Manual recovery is necessary.
    if not src.exists():raise FileNotFoundError("conversation missing; inspect audit manually")
    sleep_run(src,cpath)
    proposition=run_import(cpath,ppath)
    memory=json.loads(src.read_text(encoding="utf-8-sig"))
    candidate=json.loads(cpath.read_text(encoding="utf-8-sig"))
    evid=evidence_record(memory,candidate)
    if epath.exists():
        if json.loads(epath.read_text(encoding="utf-8-sig"))!=evid:
            raise ValueError("existing evidence differs")
    else:
        write_json_atomic(evid,epath)
    saved=json.loads(epath.read_text(encoding="utf-8-sig"))
    allowed,reason=verify_bundle(memory,candidate,proposition,saved)
    if not allowed:
        return {"version":VERSION,"mode":"APPLY","conversation_id":memory["conversation_id"],
             "deleted":False,"reason":reason,"candidate_count":len(candidate["candidates"]),
             "uncovered_turns":len(saved["uncovered_turns"])}
    pre={"version":VERSION,"phase":"PRE_DELETE",
        "conversation_id":memory["conversation_id"],
        "conversation_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
        "candidate_sha256":hashlib.sha256(cpath.read_bytes()).hexdigest(),
        "proposition_sha256":hashlib.sha256(ppath.read_bytes()).hexdigest(),
        "evidence_sha256":hashlib.sha256(epath.read_bytes()).hexdigest()}
    write_json_atomic(pre,apath)
    # This is intentionally not concurrency-safe; no other writer may modify
    # the conversation directory during this operation.
    if hashlib.sha256(src.read_bytes()).hexdigest()!=pre["conversation_sha256"]:
        raise ValueError("conversation changed during commit")
    src.unlink()
    write_json_atomic({**pre,"phase":"COMPLETED","deleted":True},apath)
    return {"version":VERSION,"mode":"APPLY","conversation_id":memory["conversation_id"],
        "deleted":True,"reason":reason,"candidate_count":len(candidate["candidates"]),
        "uncovered_turns":0}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conversation",required=True)
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--propositions",required=True)
    ap.add_argument("--evidence",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--confirm-delete",action="store_true")
    a=ap.parse_args()
    result=integrate(a.conversation,a.candidates,a.propositions,a.evidence,a.audit,
        apply=a.apply,confirm_delete=a.confirm_delete)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
