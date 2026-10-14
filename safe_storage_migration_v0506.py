#!/usr/bin/env python3
"""LLM_CHA v0.5.6: safe compact evidence migration and recovery.

Single writer only. Writes a compact artifact, checks exact reconstruction,
then commits a migration receipt. Original conversation is NEVER deleted.
An existing mismatched artifact or receipt fails closed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from benchmark_compact_evidence_v0502 import pack,verify,nbytes
from conversation_resource_memory_v042866 import validate,write_json_atomic
from conversation_sleep_backend_v042868 import fingerprint

VERSION="v0.5.6"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read_source(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():raise ValueError("invalid source")
    raw=p.read_bytes()
    memory=json.loads(raw.decode("utf-8-sig"))
    validate(memory)
    if memory["active"] or memory["status"]=="SLEEP_IN_PROGRESS":
        raise ValueError("source active or sleep in progress")
    return memory,sha(raw)

def paths(source,destination,receipt):
    a,b,c=[Path(p).resolve() for p in (source,destination,receipt)]
    if len({a,b,c})!=3:raise ValueError("source, artifact and receipt must differ")
    if b.parent==a.parent or c.parent==a.parent:
        raise ValueError("artifact/receipt must be outside source directory")
    if any(Path(p).is_symlink() for p in (source,destination,receipt)):
        raise ValueError("symlinks not supported")
    return a,b,c

def migrate(source,destination,receipt,*,inject_failure=None):
    if inject_failure not in (None,"after_artifact","after_receipt"):
        raise ValueError("unsupported fault injection")
    source_path,out,log=paths(source,destination,receipt)
    memory,source_hash=read_source(source_path)
    compact=pack(memory)
    if out.exists():
        loaded=json.loads(out.read_text(encoding="utf-8-sig"))
        verify(memory,loaded)
        disposition="EXISTING_VERIFIED"
    else:
        write_json_atomic(compact,out)
        if inject_failure=="after_artifact":raise RuntimeError("injected after artifact")
        loaded=json.loads(out.read_text(encoding="utf-8-sig"))
        verify(memory,loaded)
        disposition="CREATED"
    artifact_hash=sha(out.read_bytes())
    record={"version":VERSION,"phase":"COMMITTED",
        "conversation_id":memory["conversation_id"],
        "source_fingerprint":fingerprint(memory),"source_file_sha256":source_hash,
        "artifact_file_sha256":artifact_hash,
        "source_turns":memory["last_turn"],"reconstructed_turns":len(loaded["turns"]),
        "uncovered_turns":len(loaded["uncovered_turn_ids"]),
        "source_bytes":source_path.stat().st_size,"artifact_bytes":out.stat().st_size,
        "source_retained":True,"deletion_performed":False,
        "approved_for_eviction":False}
    if log.exists():
        previous=json.loads(log.read_text(encoding="utf-8-sig"))
        if previous!=record:raise ValueError("migration receipt mismatch")
        receipt_status="EXISTING_VERIFIED"
    else:
        write_json_atomic(record,log)
        receipt_status="CREATED"
    if inject_failure=="after_receipt":raise RuntimeError("injected after receipt")
    # Verify source has not changed during this transaction.
    _,final_hash=read_source(source_path)
    if final_hash!=source_hash:raise ValueError("source changed during migration")
    return {"version":VERSION,"conversation_id":memory["conversation_id"],
            "artifact":disposition,"receipt":receipt_status,
            "turns_verified":len(loaded["turns"]),
            "bytes_delta_if_replaced":record["source_bytes"]-record["artifact_bytes"],
            "source_retained":True,"deletion_performed":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--conversation",required=True)
    p.add_argument("--compact",required=True)
    p.add_argument("--receipt",required=True)
    a=p.parse_args()
    print(json.dumps(migrate(a.conversation,a.compact,a.receipt),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
