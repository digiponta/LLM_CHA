#!/usr/bin/env python3
"""v0.5.4 fast validated incremental /sleep: checksum-sealed checkpoint.

Full source prefix is hashed each run (O(previous turns)); previously processed
turns are NOT re-extracted. Checkpoint content uses a SHA-256 integrity seal.
This does not authenticate against malicious rewrites of both payload and seal,
nor provide multi-writer isolation. No eviction, training or Fact promotion.
"""
import argparse
import hashlib
import json
import statistics
import tempfile
import time
from copy import deepcopy
from pathlib import Path
from conversation_resource_memory_v042866 import validate,write_json_atomic
from benchmark_long_conversation_resources_v042871 import make_session
from benchmark_compact_evidence_v0502 import pack
from incremental_sleep_v0503 import initialize,chain_for,digest_step
from diagnose_jdd_candidate_expansion_v042865 import expanded_candidates

VERSION="v0.5.4"
FIELDS=("texts","turns","propositions","occurrences","uncovered_turn_ids","processed_turn","source_prefix_digest","conversation_id")
def checksum(record):
    canonical={k:record[k] for k in FIELDS}
    return hashlib.sha256(json.dumps(canonical,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()

def update(memory,old=None):
    validate(memory)
    if old is None:
        result=initialize(memory)
    else:
        if old.get("version")!=VERSION or old.get("category")!="INCREMENTAL_COMPACT_EVIDENCE":
            raise ValueError("unsupported checkpoint")
        if old.get("conversation_id")!=memory["conversation_id"] or any(old.get(k) is not False for k in ("fact_promoted","train_ready","approved_for_eviction")):
            raise ValueError("unsafe checkpoint")
        n=old.get("processed_turn")
        if type(n) is not int or not 0<=n<=memory["last_turn"]:
            raise ValueError("checkpoint out of range")
        if old.get("checkpoint_sha256")!=checksum(old):
            raise ValueError("checkpoint payload checksum mismatch")
        if old["source_prefix_digest"]!=chain_for(memory["turns"][:n]):
            raise ValueError("source prefix mismatch")
        result=deepcopy(old)
    start=result["processed_turn"]
    texts={v:i for i,v in enumerate(result["texts"])}
    propositions={tuple(v):i for i,v in enumerate(result["propositions"])}
    chain=result["source_prefix_digest"]
    for turn in memory["turns"][start:]:
        tid=turn["turn_id"];value=turn["text"]
        if value not in texts:
            texts[value]=len(result["texts"]);result["texts"].append(value)
        result["turns"].append([tid,turn["speaker"],texts[value]])
        found,_=expanded_candidates(memory["conversation_id"],turn)
        if not found:result["uncovered_turn_ids"].append(tid)
        for candidate in found:
            key=(candidate["speaker"],candidate["subject"],candidate["predicate"],candidate["object"],candidate["polarity"])
            if key not in propositions:
                propositions[key]=len(result["propositions"])
                result["propositions"].append(list(key))
            result["occurrences"].append([propositions[key],tid,*candidate["source_span"]])
        chain=digest_step(chain,turn)
    result["processed_turn"]=memory["last_turn"]
    result["source_prefix_digest"]=chain
    result["version"]=VERSION
    result["checkpoint_sha256"]=checksum(result)
    return result

def equivalent(memory,checkpoint):
    full=pack(memory)
    return all(checkpoint[k]==full[k] for k in ("texts","turns","propositions","occurrences","uncovered_turn_ids"))

def commit(memory,path):
    path=Path(path)
    old=json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else None
    result=update(memory,old)
    write_json_atomic(result,path)
    if json.loads(path.read_text(encoding="utf-8-sig"))!=result:
        raise ValueError("checkpoint readback failed")
    return {"version":VERSION,"new_turns":result["processed_turn"]-(old["processed_turn"] if old else 0),
        "processed_turn":result["processed_turn"],"checkpoint_verified":True,"deletion_performed":False}

def benchmark(checkpoints=(100,500,1000),unmatched_every=0,repeats=7):
    checkpoints=tuple(checkpoints)
    if not checkpoints or sorted(set(checkpoints))!=list(checkpoints) or any(type(n) is not int or n<1 for n in checkpoints):
        raise ValueError("invalid checkpoints")
    if type(repeats) is not int or repeats<2 or type(unmatched_every) is not int or unmatched_every<0:
        raise ValueError("invalid repeats or unmatched_every")
    base=make_session(checkpoints[-1],unmatched_every)
    output=[]
    for end in checkpoints:
        partial=deepcopy(base);partial["turns"]=deepcopy(base["turns"][:end]);partial["last_turn"]=end
        partial["sleep"]={"processed_turn":0,"completed":False};partial["status"]="PENDING_SLEEP"
        prior=checkpoints[checkpoints.index(end)-1] if checkpoints.index(end) else 0
        earlier=deepcopy(partial);earlier["turns"]=deepcopy(partial["turns"][:prior]);earlier["last_turn"]=prior
        previous=update(earlier) if prior else None
        fast_times=[];full_times=[]
        for _ in range(repeats):
            start=time.perf_counter();current=update(partial,previous)
            fast_times.append((time.perf_counter()-start)*1000)
            start=time.perf_counter();reference=pack(partial)
            full_times.append((time.perf_counter()-start)*1000)
        if not equivalent(partial,current):raise ValueError("incremental/full mismatch")
        output.append({"turns":end,"new_turns":end-prior,"repeats":repeats,
          "fast_median_ms":round(statistics.median(fast_times),4),
          "fast_min_ms":round(min(fast_times),4),
          "fast_max_ms":round(max(fast_times),4),
          "full_median_ms":round(statistics.median(full_times),4),
          "full_min_ms":round(min(full_times),4),
          "full_max_ms":round(max(full_times),4),
          "equivalent_to_full":True,"uncovered_turns":len(current["uncovered_turn_ids"])})
    return {"version":VERSION,"mode":"SYNTHETIC_CHECKPOINT_OPTIMIZATION",
        "rows":output,"training_performed":False,"deletion_performed":False,
        "limitations":["Old source prefix hashing remains O(n) and is not a cryptographic trust anchor.",
          "Checkpoint digest detects accidental changes but not attacker recomputation.",
          "Benchmarks use repetitive synthetic conversations and one process.",
          "No multi-writer locks, crash-atomic multi-file transactions, or eviction."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoints",type=int,nargs="+",default=[100,500,1000])
    p.add_argument("--unmatched-every",type=int,default=0)
    p.add_argument("--repeats",type=int,default=7)
    p.add_argument("--output",default="results/checkpoint_optimization_v0504.json")
    a=p.parse_args()
    report=benchmark(a.checkpoints,a.unmatched_every,a.repeats)
    write_json_atomic(report,a.output)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
