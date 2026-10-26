"""Explicit, backup-first reconciliation of a verified semantic checkpoint.

Default is a read-only inspection. --apply requires --checkpoint and full memory
coverage, and refuses to overwrite an already populated learning state.
This reconciles bookkeeping only, never asserts weight-level answer quality.
"""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from semantic_sleep_learning_v10131 import load_nagato_semantic_memory

def inspect(state_path, memory_path, checkpoint_path):
    import torch
    state_path=Path(state_path); memory_path=Path(memory_path); checkpoint_path=Path(checkpoint_path)
    rows=load_nagato_semantic_memory(memory_path)
    memory={str(r.get("fingerprint","")) for r in rows}
    if not memory or "" in memory or len(memory)!=len(rows):
        raise ValueError("Semantic Memory must have nonempty unique fingerprints")
    if not checkpoint_path.is_file():
        raise FileNotFoundError(checkpoint_path)
    checkpoint=torch.load(checkpoint_path,map_location="cpu",weights_only=True)
    metadata=checkpoint.get("metadata",{})
    if not isinstance(metadata,dict) or not isinstance(metadata.get("trained_fingerprints"),(list,tuple,set)):
        raise ValueError("Checkpoint lacks trained_fingerprints metadata")
    fingerprints={str(x) for x in metadata["trained_fingerprints"]}
    if not state_path.is_file():
        raise FileNotFoundError(state_path)
    state=json.loads(state_path.read_text(encoding="utf-8-sig"))
    if not isinstance(state,dict) or not isinstance(state.get("trained_fingerprints"),list):
        raise ValueError("Unexpected learning state format")
    existing=set(map(str,state["trained_fingerprints"]))
    complete=memory.issubset(fingerprints)
    safe=complete and not existing and bool(fingerprints)
    return {
        "checkpoint":str(checkpoint_path),
        "memory_total":len(memory),
        "checkpoint_total":len(fingerprints),
        "memory_covered":len(memory & fingerprints),
        "learning_state_total":len(existing),
        "status":"READY_FOR_EXPLICIT_RECONCILIATION" if safe else "REVIEW_REQUIRED",
        "can_apply":safe,
        "weights_verified":False,
        "fingerprints":sorted(fingerprints),
    }

def reconcile(state_path,memory_path,checkpoint_path,apply=False):
    report=inspect(state_path,memory_path,checkpoint_path)
    if not apply:
        report.pop("fingerprints")
        return report
    if not report["can_apply"]:
        raise ValueError("Refusing to modify state: review required")
    path=Path(state_path)
    original=path.read_bytes()
    state=json.loads(original.decode("utf-8-sig"))
    # Fixed .bak path must not be overwritten; preserve the first snapshot.
    backup=path.with_name(path.name+".pre-reconcile.bak")
    with backup.open("xb") as dest:
        dest.write(original)
        dest.flush()
        os.fsync(dest.fileno())
    state["trained_fingerprints"]=report["fingerprints"]
    temp=None
    try:
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,
                prefix=path.name+".",suffix=".tmp",delete=False) as f:
            temp=Path(f.name)
            json.dump(state,f,ensure_ascii=False,indent=2)
            f.write("\n");f.flush();os.fsync(f.fileno())
        if path.read_bytes()!=original:
            raise RuntimeError("Learning state changed during reconciliation")
        os.replace(temp,path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()
    report.pop("fingerprints")
    report["status"]="RECONCILED_METADATA_ONLY"
    report["backup"]=str(backup)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",required=True,type=Path)
    p.add_argument("--memory",default="data/nagato_semantic_memory_v10131.jsonl",type=Path)
    p.add_argument("--learning-state",default="data/chat_learning_state.json",type=Path)
    p.add_argument("--apply",action="store_true",help="Explicitly write learning state after creating backup")
    a=p.parse_args()
    print(json.dumps(reconcile(a.learning_state,a.memory,a.checkpoint,a.apply),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
