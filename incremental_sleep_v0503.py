#!/usr/bin/env python3
"""LLM_CHA v0.5.3: incremental /sleep compact evidence projection.

Single-writer local research prototype. New turns only are parsed. The source
prefix is authenticated by a rolling SHA-256 chain. Save artifact atomically,
verify readback, and update the checkpoint within that same artifact.
No conversation deletion, training, or Fact promotion.
"""
import argparse
import hashlib
import json
import time
from copy import deepcopy
from pathlib import Path

from benchmark_compact_evidence_v0502 import pack, nbytes
from benchmark_long_conversation_resources_v042871 import make_session
from conversation_resource_memory_v042866 import validate, write_json_atomic
from diagnose_jdd_candidate_expansion_v042865 import expanded_candidates

VERSION="v0.5.3"
SEED=hashlib.sha256(b"LLM_CHA_INCREMENTAL_V053").hexdigest()

def digest_step(previous, turn):
    data=json.dumps(turn,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return hashlib.sha256((previous+"|"+data).encode("utf-8")).hexdigest()

def chain_for(turns):
    chain=SEED
    for turn in turns:chain=digest_step(chain,turn)
    return chain

def initialize(memory):
    validate(memory)
    result={"version":VERSION,"category":"INCREMENTAL_COMPACT_EVIDENCE",
        "conversation_id":memory["conversation_id"],"processed_turn":0,
        "source_prefix_digest":SEED,"texts":[],"turns":[],
        "propositions":[],"occurrences":[],"uncovered_turn_ids":[],
        "truth_state":"UNVERIFIED","train_ready":False,
        "fact_promoted":False,"approved_for_eviction":False}
    return result

def update(memory,existing=None):
    validate(memory)
    if existing is None:existing=initialize(memory)
    if existing.get("category")!="INCREMENTAL_COMPACT_EVIDENCE" or existing.get("conversation_id")!=memory["conversation_id"]:
        raise ValueError("invalid incremental artifact identity")
    if any(existing.get(k) is not False for k in ("train_ready","fact_promoted","approved_for_eviction")):
        raise ValueError("unsafe flags")
    old=existing.get("processed_turn")
    if type(old) is not int or not 0<=old<=memory["last_turn"]:
        raise ValueError("invalid checkpoint")
    if existing.get("source_prefix_digest")!=chain_for(memory["turns"][:old]):
        raise ValueError("source prefix changed")
    # Validate internal integrity by replaying the existing prefix against the
    # canonical projection; do not re-run extraction on committed old turns.
    prefix=deepcopy(memory)
    prefix["turns"]=deepcopy(memory["turns"][:old])
    prefix["last_turn"]=old
    prefix["sleep"]={"processed_turn":0,"completed":False}
    prefix["status"]="PENDING_SLEEP"
    expected=pack(prefix)
    if (existing["texts"]!=expected["texts"] or existing["turns"]!=expected["turns"]
        or existing["propositions"]!=expected["propositions"]
        or existing["occurrences"]!=expected["occurrences"]
        or existing["uncovered_turn_ids"]!=expected["uncovered_turn_ids"]):
        raise ValueError("existing compact evidence was modified")
    staged=deepcopy(existing)
    texts={value:i for i,value in enumerate(staged["texts"])}
    defs={tuple(value):i for i,value in enumerate(staged["propositions"])}
    covered=set()
    chain=staged["source_prefix_digest"]
    for turn in memory["turns"][old:]:
        tid=turn["turn_id"];txt=turn["text"]
        if txt not in texts:
            texts[txt]=len(staged["texts"]);staged["texts"].append(txt)
        staged["turns"].append([tid,turn["speaker"],texts[txt]])
        candidates,guards=expanded_candidates(memory["conversation_id"],turn)
        for c in candidates:
            key=(c["speaker"],c["subject"],c["predicate"],c["object"],c["polarity"])
            if key not in defs:
                defs[key]=len(staged["propositions"])
                staged["propositions"].append(list(key))
            staged["occurrences"].append([defs[key],tid,*c["source_span"]])
            covered.add(tid)
        if tid not in covered:staged["uncovered_turn_ids"].append(tid)
        chain=digest_step(chain,turn)
    staged["processed_turn"]=memory["last_turn"]
    staged["source_prefix_digest"]=chain
    # Equivalence of the update to a fresh full projection is a test/benchmark
    # responsibility: this method avoids extracting old turns on update.
    return staged

def commit(memory,path):
    dest=Path(path)
    if dest.exists():
        existing=json.loads(dest.read_text(encoding="utf-8-sig"))
    else:existing=None
    updated=update(memory,existing)
    write_json_atomic(updated,dest)
    readback=json.loads(dest.read_text(encoding="utf-8-sig"))
    if readback!=updated:raise ValueError("readback mismatch")
    return {"version":VERSION,"processed_turn":readback["processed_turn"],
            "new_turns":readback["processed_turn"]-(existing["processed_turn"] if existing else 0),
            "unique_utterances":len(readback["texts"]),
            "unique_propositions":len(readback["propositions"]),
            "uncovered_turns":len(readback["uncovered_turn_ids"]),
            "bytes":nbytes(readback),"deletion_performed":False}

def benchmark(checkpoints=(100,500,1000),unmatched_every=0):
    values=tuple(checkpoints)
    if not values or any(type(x) is not int or x<=0 for x in values) or tuple(sorted(set(values)))!=values:
        raise ValueError("checkpoints must be increasing positive integers")
    if type(unmatched_every) is not int or unmatched_every<0:raise ValueError("invalid unmatched_every")
    full=make_session(values[-1],unmatched_every)
    artifact=None;rows=[]
    for n in values:
        partial=deepcopy(full)
        partial["turns"]=deepcopy(full["turns"][:n]);partial["last_turn"]=n
        partial["sleep"]={"processed_turn":0,"completed":False}
        partial["status"]="PENDING_SLEEP"
        start=time.perf_counter()
        prior=artifact["processed_turn"] if artifact else 0
        artifact=update(partial,artifact)
        incremental_seconds=time.perf_counter()-start
        start=time.perf_counter()
        expected=pack(partial)
        full_seconds=time.perf_counter()-start
        equal=(artifact["texts"]==expected["texts"]
          and artifact["turns"]==expected["turns"]
          and artifact["propositions"]==expected["propositions"]
          and artifact["occurrences"]==expected["occurrences"]
          and artifact["uncovered_turn_ids"]==expected["uncovered_turn_ids"])
        if not equal:raise ValueError("incremental vs full mismatch")
        rows.append({"turns":n,"new_turns":n-prior,
          "incremental_seconds":round(incremental_seconds,6),
          "full_rebuild_seconds":round(full_seconds,6),
          "equivalent_to_full":equal,"unique_utterances":len(artifact["texts"]),
          "unique_propositions":len(artifact["propositions"]),
          "uncovered_turns":len(artifact["uncovered_turn_ids"]),
          "incremental_bytes":nbytes(artifact),"full_projection_bytes":nbytes(expected)})
    return {"version":VERSION,"mode":"SYNTHETIC_INCREMENTAL_SLEEP",
      "rows":rows,"deletion_performed":False,"training_performed":False,
      "limitations":["Single-writer prototype without multi-file transactions.",
        "Prefix-integrity verification reserializes old turns and checks the existing structure.",
        "Synthetic repeats are not a language understanding benchmark.",
        "No automatic eviction or Fact promotion."]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoints",nargs="+",type=int,default=[100,500,1000])
    ap.add_argument("--unmatched-every",type=int,default=0)
    ap.add_argument("--output",default="results/incremental_sleep_v0503.json")
    a=ap.parse_args()
    report=benchmark(a.checkpoints,a.unmatched_every)
    write_json_atomic(report,a.output)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
