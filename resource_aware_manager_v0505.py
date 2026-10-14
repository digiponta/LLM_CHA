#!/usr/bin/env python3
"""LLM_CHA v0.5.5 resource-aware tiering planner (dry-run only).

Plans retention tiers based on source, compact and protected checkpoint sizes.
No files are deleted/moved/rewritten; compaction is hypothetical until validated.
"""
import argparse
import json
from pathlib import Path
from benchmark_long_conversation_resources_v042871 import make_session
from benchmark_compact_evidence_v0502 import pack,nbytes
from conversation_resource_memory_v042866 import validate,write_json_atomic

VERSION="v0.5.5"
def measure(memory):
    validate(memory)
    compact=pack(memory)
    count=len(compact["uncovered_turn_ids"])
    return {"conversation_id":memory["conversation_id"],"turns":memory["last_turn"],
      "active":memory["active"],"status":memory["status"],
      "source_bytes":nbytes(memory),"compact_bytes":nbytes(compact),
      "uncovered_turns":count,"reconstructible":True,
      "approved_for_eviction":False}

def plan(records,budget_bytes):
    if type(budget_bytes) is not int or budget_bytes<0:raise ValueError("invalid budget")
    if not isinstance(records,list):raise ValueError("records must be list")
    if len({r["conversation_id"] for r in records})!=len(records):
        raise ValueError("duplicate conversation IDs")
    inspected=[measure(r) for r in records]
    source_total=sum(i["source_bytes"] for i in inspected)
    projected_total=sum(i["compact_bytes"] for i in inspected)
    rows=[]
    for info in inspected:
        # The projection can be used as a test candidate, but no source is
        # eligible for eviction without a separate durable evidence gate.
        if info["active"]:tier="HOT_ACTIVE"
        elif info["status"]=="SLEEP_IN_PROGRESS":tier="HOT_SLEEP_IN_PROGRESS"
        elif info["uncovered_turns"]:tier="WARM_UNCOVERED_PROTECTED"
        elif info["status"]!="SLEEP_COMPLETED":tier="WARM_PENDING_SLEEP"
        else:tier="COLD_REVIEW_REQUIRED"
        rows.append({**info,"tier":tier,
          "projected_savings_bytes":info["source_bytes"]-info["compact_bytes"],
          "recommended_action":"PRESERVE_SOURCE_AND_REVIEW",
          "deletion_allowed":False})
    return {"version":VERSION,"mode":"DRY_RUN_RESOURCE_PRESSURE",
      "budget_bytes":budget_bytes,"source_total_bytes":source_total,
      "projected_compact_total_bytes":projected_total,
      "projected_delta_bytes":source_total-projected_total,
      "source_over_budget":source_total>budget_bytes,
      "compact_projection_over_budget":projected_total>budget_bytes,
      "records":rows,"actual_bytes_freed":0,
      "deletion_performed":False,"runtime_modified":False,
      "limitations":["Projected compact size is not a replacement for full evidence system accounting.",
        "No source can be removed by this planner.",
        "A completed /sleep checkpoint alone is insufficient authorization for deletion.",
        "All projections retain every utterance; only repeated strings are dictionary-coded."]}

def benchmark(turn_counts=(100,500,1000),unmatched_every=0,budget_bytes=150000):
    if not turn_counts or any(type(x) is not int or x<1 for x in turn_counts):
        raise ValueError("turn counts must be positive")
    if type(unmatched_every) is not int or unmatched_every<0:
        raise ValueError("invalid unmatched frequency")
    if type(budget_bytes) is not int or budget_bytes<0:
        raise ValueError("invalid budget")
    records=[make_session(n,unmatched_every) for n in turn_counts]
    return plan(records,budget_bytes)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--turn-counts",type=int,nargs="+",default=[100,500,1000])
    p.add_argument("--unmatched-every",type=int,default=0)
    p.add_argument("--budget-bytes",type=int,default=150000)
    p.add_argument("--output",default="results/resource_aware_v0505.json")
    a=p.parse_args()
    result=benchmark(a.turn_counts,a.unmatched_every,a.budget_bytes)
    write_json_atomic(result,Path(a.output))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
