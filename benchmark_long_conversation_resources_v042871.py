#!/usr/bin/env python3
"""LLM_CHA v0.4.28.71: synthetic long-conversation resource benchmark.

Measures actual byte sizes and timings; reports no model-quality or real-dialogue
claims. Uses temporary files; dry-run integration by default, no deletion.
"""
import argparse
import json
import tempfile
import time
from pathlib import Path

from conversation_resource_memory_v042866 import (
 new_conversation,append_turn,close_session,write_json_atomic)
from conversation_sleep_backend_v042868 import run as sleep_run
from proposition_memory_lifecycle_v042869 import run_import
from sleep_eviction_integration_v042870 import evidence_record,verify_bundle

VERSION="v0.4.28.71"
MATCHED=("私は音楽が好き","私は映画が好き","私は車を持っています")
UNMATCHED="今日はいい天気ですね"

def make_session(turns,unmatched_every=0):
    if type(turns) is not int or turns<1:raise ValueError("turn count must be positive")
    if type(unmatched_every) is not int or unmatched_every<0:raise ValueError("invalid unmatched frequency")
    memory=new_conversation(f"synthetic-{turns}-{unmatched_every}")
    for i in range(turns):
        text=(UNMATCHED if unmatched_every and (i+1)%unmatched_every==0
              else MATCHED[i%len(MATCHED)])
        append_turn(memory,"A" if i%2==0 else "B",text)
    close_session(memory)
    return memory

def one_benchmark(turns,unmatched_every=0):
    with tempfile.TemporaryDirectory(prefix="llm-cha-benchmark-") as temp:
        base=Path(temp)
        conversations=base/"conversations";artifacts=base/"artifacts"
        conversations.mkdir();artifacts.mkdir()
        source=conversations/"synthetic.conversation.json"
        cand=artifacts/"candidate.json";prop=artifacts/"proposition.json"
        evid=artifacts/"evidence.json"
        start=time.perf_counter()
        memory=make_session(turns,unmatched_every)
        write_json_atomic(memory,source)
        build_seconds=time.perf_counter()-start
        conversation_bytes=source.stat().st_size
        start=time.perf_counter()
        sleep_result=sleep_run(source,cand)
        sleep_seconds=time.perf_counter()-start
        start=time.perf_counter()
        proposition=run_import(cand,prop)
        candidate=json.loads(cand.read_text(encoding="utf-8"))
        updated=json.loads(source.read_text(encoding="utf-8"))
        evidence=evidence_record(updated,candidate)
        write_json_atomic(evidence,evid)
        allowed,reason=verify_bundle(updated,candidate,proposition,evidence)
        verify_seconds=time.perf_counter()-start
        candidate_bytes=cand.stat().st_size
        proposition_bytes=prop.stat().st_size
        evidence_bytes=evid.stat().st_size
        artifacts_bytes=candidate_bytes+proposition_bytes+evidence_bytes
        # Only report prospective removal; leave conversation on disk.
        return {"turns":turns,"unmatched_every":unmatched_every,
            "build_seconds":round(build_seconds,6),
            "sleep_seconds":round(sleep_seconds,6),
            "proposition_evidence_seconds":round(verify_seconds,6),
            "conversation_bytes":conversation_bytes,
            "candidate_bytes":candidate_bytes,
            "proposition_bytes":proposition_bytes,
            "evidence_bytes":evidence_bytes,
            "artifacts_total_bytes":artifacts_bytes,
            "bytes_before_eviction":conversation_bytes+artifacts_bytes,
            "potential_bytes_freed":conversation_bytes if allowed else 0,
            "net_bytes_after_eviction":artifacts_bytes if allowed else conversation_bytes+artifacts_bytes,
            "candidate_count":sleep_result["candidates"],
            "uncovered_turns":len(evidence["uncovered_turns"]),
            "evidence_turn_coverage":round((turns-len(evidence["uncovered_turns"]))/turns,6),
            "deletion_gate":reason,"deletion_permitted":allowed,
            "deletion_performed":False,
            "model_response_quality":None,"fact_accuracy":None}

def benchmark(turn_counts=(100,500,1000),unmatched_every=0):
    sizes=tuple(turn_counts)
    if not sizes or any(type(n) is not int or n<1 for n in sizes):
        raise ValueError("invalid turn counts")
    rows=[one_benchmark(n,unmatched_every) for n in sizes]
    return {"version":VERSION,"mode":"SYNTHETIC_LONG_CONVERSATION_RESOURCE_BENCHMARK",
         "rows":rows,"training_performed":False,"runtime_modified":False,
         "source_corpus":"synthetic","dry_run_only":True,
         "limitations":["Timings are machine-dependent and include JSON serialization.",
                        "Generated repetitive turns do not establish conversational understanding.",
                        "Evidence store includes full matched utterances, which may exceed the source size.",
                        "No actual eviction, recovery fault injection, or model response evaluation."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--turn-counts",type=int,nargs="+",default=[100,500,1000])
    p.add_argument("--unmatched-every",type=int,default=0)
    p.add_argument("--output",default="results/long_conversation_resources_v042871.json")
    a=p.parse_args()
    result=benchmark(a.turn_counts,a.unmatched_every)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    write_json_atomic(result,out)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
