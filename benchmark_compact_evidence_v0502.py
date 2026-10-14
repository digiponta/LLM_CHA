#!/usr/bin/env python3
"""LLM_CHA v0.5.2: compact evidence store with reversible turn coverage.

Dictionary-encodes repeated utterances and propositions; references keep
speaker, turn ordering and exact text. No deletion, fact promotion or training.
"""
import argparse
import json
from pathlib import Path
from benchmark_long_conversation_resources_v042871 import make_session
from conversation_sleep_backend_v042868 import extract
from conversation_resource_memory_v042866 import validate,write_json_atomic

VERSION="v0.5.2"
def nbytes(obj):
    return len((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
def pack(memory):
    validate(memory)
    extracted=extract(memory)
    texts=[];text_ids={};definitions=[];definition_ids={}
    turns=[]
    for t in memory["turns"]:
        value=t["text"]
        if value not in text_ids:
            text_ids[value]=len(texts);texts.append(value)
        turns.append([t["turn_id"],t["speaker"],text_ids[value]])
    occurrences=[]
    for c in extracted["candidates"]:
        key=(c["speaker"],c["subject"],c["predicate"],c["object"],c["polarity"])
        if key not in definition_ids:
            definition_ids[key]=len(definitions)
            definitions.append(list(key))
        occurrences.append([definition_ids[key],c["source_turn"],*c["source_span"]])
    return {"version":VERSION,"category":"COMPACT_EVIDENCE_PROJECTION",
        "conversation_id":memory["conversation_id"],
        "source_fingerprint":extracted["source_fingerprint"],
        "texts":texts,"turns":turns,
        "propositions":definitions,"occurrences":occurrences,
        "uncovered_turn_ids":[t["turn_id"] for t in memory["turns"]
            if t["turn_id"] not in {o[1] for o in occurrences}],
        "truth_state":"UNVERIFIED","fact_promoted":False,
        "train_ready":False,"approved_for_eviction":False}

def verify(memory,packed):
    validate(memory)
    expected=pack(memory)
    if packed!=expected:raise ValueError("compact store provenance/content mismatch")
    recovered=[]
    for turn_id,speaker,text_idx in packed["turns"]:
        recovered.append((turn_id,speaker,packed["texts"][text_idx]))
    actual=[(t["turn_id"],t["speaker"],t["text"]) for t in memory["turns"]]
    if recovered!=actual:raise ValueError("turn reconstruction mismatch")
    return True

def compare(turns,unmatched_every=0):
    m=make_session(turns,unmatched_every)
    source=extract(m)
    packed=pack(m)
    verify(m,packed)
    return {"turns":turns,"unmatched_every":unmatched_every,
        "conversation_bytes":nbytes(m),"candidate_bytes":nbytes(source),
        "compact_evidence_bytes":nbytes(packed),
        "unique_utterances":len(packed["texts"]),
        "unique_propositions":len(packed["propositions"]),
        "candidate_count":len(packed["occurrences"]),
        "uncovered_turns":len(packed["uncovered_turn_ids"]),
        "bytes_saved_vs_conversation":nbytes(m)-nbytes(packed),
        "bytes_saved_vs_candidates":nbytes(source)-nbytes(packed),
        "all_turns_reconstructed":True,"deletion_performed":False,
        "approved_for_eviction":False}

def benchmark(turn_counts=(100,500,1000),unmatched_every=0):
    if not turn_counts or any(type(n) is not int or n<1 for n in turn_counts):
        raise ValueError("invalid turn counts")
    if type(unmatched_every) is not int or unmatched_every<0:
        raise ValueError("invalid unmatched frequency")
    return {"version":VERSION,"mode":"SYNTHETIC_COMPACT_EVIDENCE_BENCHMARK",
        "rows":[compare(n,unmatched_every) for n in turn_counts],
        "dry_run_only":True,"runtime_modified":False,"training_performed":False,
        "limitations":["Exact repeated utterances make this synthetic corpus unusually compressible.",
          "Full utterances are retained in the dictionary, including uncovered turns.",
          "This is not wired into live eviction; no automatic deletion is permitted.",
          "Byte counts are formatted JSON projections, not full pipeline accounting.",
          "Verification checks deterministic reconstruction, not semantic accuracy."]}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--turn-counts",type=int,nargs="+",default=[100,500,1000])
    p.add_argument("--unmatched-every",type=int,default=0)
    p.add_argument("--output",default="results/compact_evidence_v0502.json")
    a=p.parse_args()
    result=benchmark(a.turn_counts,a.unmatched_every)
    write_json_atomic(result,Path(a.output))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
