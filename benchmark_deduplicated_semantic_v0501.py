#!/usr/bin/env python3
"""LLM_CHA v0.5.1: provenance-preserving deduplicated proposition projection.

Research/benchmark artifact only. Never automatically promotes to Fact,
trains a model, or authorizes deleting original conversation records.
"""
import argparse
import hashlib
import json
from pathlib import Path
from benchmark_long_conversation_resources_v042871 import make_session
from conversation_sleep_backend_v042868 import extract
from conversation_resource_memory_v042866 import write_json_atomic

VERSION="v0.5.1"

def utf8_size(obj):
    return len((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))

def build(memory):
    raw=extract(memory)
    entries={}
    for p in raw["candidates"]:
        key=(p["speaker"],p["subject"],p["predicate"],p["object"],p["polarity"])
        if key not in entries:
            entries[key]={"speaker":p["speaker"],"subject":p["subject"],
                "predicate":p["predicate"],"object":p["object"],
                "polarity":p["polarity"],"occurrences":[]}
        entries[key]["occurrences"].append([p["source_turn"],p["source_span"][0],
                                                p["source_span"][1]])
    propositions=[]
    for key in sorted(entries):
        item=entries[key]
        item["occurrences"].sort()
        item["id"]=hashlib.sha256(json.dumps(key,ensure_ascii=False,
            separators=(",",":")).encode("utf-8")).hexdigest()[:16]
        propositions.append(item)
    covered={row[0] for p in propositions for row in p["occurrences"]}
    uncovered=[t["turn_id"] for t in memory["turns"] if t["turn_id"] not in covered]
    return {"version":VERSION,"category":"DEDUPLICATED_PROPOSITION_PROJECTION",
        "conversation_id":memory["conversation_id"],
        "source_fingerprint":raw["source_fingerprint"],
        "source_turns":memory["last_turn"],
        "propositions":propositions,
        "uncovered_turn_ids":uncovered,"truth_state":"UNVERIFIED",
        "fact_promoted":False,"train_ready":False,"approved_for_eviction":False}

def verify(memory,packed):
    original=extract(memory)
    if packed.get("category")!="DEDUPLICATED_PROPOSITION_PROJECTION" or packed.get("approved_for_eviction") is not False:
        raise ValueError("invalid projection")
    if packed.get("conversation_id")!=memory["conversation_id"] or packed.get("source_fingerprint")!=original["source_fingerprint"]:
        raise ValueError("source mismatch")
    expected=[]
    for p in original["candidates"]:
        expected.append((p["speaker"],p["subject"],p["predicate"],p["object"],
            p["polarity"],p["source_turn"],p["source_span"][0],p["source_span"][1]))
    recovered=[]
    for p in packed["propositions"]:
        for turn,start,end in p["occurrences"]:
            recovered.append((p["speaker"],p["subject"],p["predicate"],p["object"],
                              p["polarity"],turn,start,end))
    if sorted(expected)!=sorted(recovered):
        raise ValueError("proposition occurrence loss or mutation")
    coverage={p["source_turn"] for p in original["candidates"]}
    if packed.get("uncovered_turn_ids")!=[t["turn_id"] for t in memory["turns"] if t["turn_id"] not in coverage]:
        raise ValueError("uncovered-turn mismatch")
    return True

def compare(turns,unmatched_every=0):
    memory=make_session(turns,unmatched_every)
    raw=extract(memory)
    packed=build(memory)
    verify(memory,packed)
    raw_size=utf8_size(raw);packed_size=utf8_size(packed)
    return {"turns":turns,"unmatched_every":unmatched_every,
        "candidate_count":len(raw["candidates"]),
        "unique_propositions":len(packed["propositions"]),
        "uncovered_turns":len(packed["uncovered_turn_ids"]),
        "raw_candidate_bytes":raw_size,"deduplicated_bytes":packed_size,
        "bytes_saved":raw_size-packed_size,
        "size_ratio":round(packed_size/raw_size,6),
        "occurrences_verified":True,"deletion_performed":False,
        "approved_for_eviction":False}

def benchmark(turn_counts=(100,500,1000),unmatched_every=0):
    if not turn_counts or any(type(n) is not int or n<1 for n in turn_counts):
        raise ValueError("positive turn counts required")
    if type(unmatched_every) is not int or unmatched_every<0:
        raise ValueError("invalid unmatched_every")
    return {"version":VERSION,"mode":"SYNTHETIC_DEDUPLICATED_SEMANTIC_PROJECTION",
        "rows":[compare(n,unmatched_every) for n in turn_counts],
        "dry_run_only":True,"training_performed":False,"runtime_modified":False,
        "limitations":["Synthetic repeated utterances overestimate real-world deduplication.",
          "Comparison covers candidate artifact versus compact projection only, not the entire memory pipeline.",
          "Occurrence provenance is preserved, but original utterance text is not; no source deletion is authorized.",
          "Proposition identity is speaker-scoped; apparent facts are not verified."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--turn-counts",nargs="+",type=int,default=[100,500,1000])
    p.add_argument("--unmatched-every",type=int,default=0)
    p.add_argument("--output",default="results/deduplicated_semantic_v0501.json")
    a=p.parse_args()
    result=benchmark(a.turn_counts,a.unmatched_every)
    write_json_atomic(result,Path(a.output))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
