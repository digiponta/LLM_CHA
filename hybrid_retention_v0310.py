"""v0.3.1 hybrid topic retention: bounded explicit pin budget + frequency/recency.

Experimental standalone evaluator. No mutation of Truth State, Corpus,
Semantic Memory, checkpoint, or LLM weights. Never auto-unpin a protected topic.
"""
from __future__ import annotations
import json
from pathlib import Path
from adaptive_retention_eval_v023351 import Event, simulate
from retention_cross_scenario_v0300 import scenarios

def hybrid(events:list[Event], capacity:int=4, pin_budget:int|None=None)->dict:
    if type(capacity) is not int or not 1<=capacity<=16:
        raise ValueError("capacity must be 1..16")
    if pin_budget is None:
        pin_budget=max(1,capacity//2)
    if type(pin_budget) is not int or not 0<=pin_budget<capacity:
        raise ValueError("pin budget must be 0..capacity-1")
    present:dict[str,dict]={}
    counts:dict[str,int]={}
    hits=important_hits=important_queries=queries=evictions=refusals=pin_denials=0
    for step,e in enumerate(events,1):
        if not isinstance(e,Event) or e.kind not in ("observe","query") or not isinstance(e.topic,str) or not e.topic.strip():
            raise ValueError("invalid event")
        name=e.topic
        if e.kind=="query":
            queries+=1
            hit=name in present
            hits+=int(hit)
            if e.important:
                important_queries+=1
                important_hits+=int(hit)
            continue
        counts[name]=counts.get(name,0)+1
        if name in present:
            present[name]["last"]=step
            present[name]["frequency"]=counts[name]
            if e.important and not present[name]["pin"]:
                if sum(x["pin"] for x in present.values())<pin_budget:
                    present[name]["pin"]=True
                else:
                    pin_denials+=1
            continue
        want_pin=bool(e.important)
        allowed_pin=want_pin and sum(x["pin"] for x in present.values())<pin_budget
        if want_pin and not allowed_pin:
            pin_denials+=1
        if len(present)==capacity:
            eligible=[(key,row) for key,row in present.items() if not row["pin"]]
            if not eligible:
                refusals+=1
                continue
            # Frequency first, recency second, deterministic lexical tie-break.
            victim=min(eligible,key=lambda item:(item[1]["frequency"],item[1]["last"],item[0]))[0]
            del present[victim]
            evictions+=1
        present[name]={"last":step,"frequency":counts[name],"pin":allowed_pin}
    return {"policy":"hybrid_pin_budget","capacity":capacity,"pin_budget":pin_budget,
            "queries":queries,"query_hits":hits,
            "return_success_rate":hits/queries if queries else None,
            "important_queries":important_queries,
            "important_retention_rate":important_hits/important_queries if important_queries else None,
            "evictions":evictions,"protected_insertion_refusals":refusals,
            "pin_budget_denials":pin_denials,
            "pinned_topics":sorted(k for k,v in present.items() if v["pin"]),
            "final_topics":sorted(present),
            "capacity_compliant":len(present)<=capacity,
            "budget_compliant":sum(v["pin"] for v in present.values())<=pin_budget}

def compare(capacities=(2,4,8))->dict:
    rows=[]
    for name,events in scenarios().items():
        for capacity in capacities:
            for policy in ("lru","frequency","pin_adaptive"):
                rows.append({"scenario":name,**simulate(events,policy,capacity)})
            rows.append({"scenario":name,**hybrid(events,capacity)})
    return {"version":"v0.3.1","scenario_count":len(scenarios()),
            "capacities":list(capacities),"rows":rows,
            "notes":"synthetic fixture importance only; pin-budget denial means no hard pin was created, not rejected topic insertion"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--report",default="results/hybrid_retention_v0310.json")
    args=p.parse_args()
    report=compare()
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"v0.3.1 scenarios={report['scenario_count']} rows={len(report['rows'])}")
    for row in report["rows"]:
        if row["policy"]=="hybrid_pin_budget":
            print(f"{row['scenario']:16s} cap={row['capacity']} "
                  f"return={row['return_success_rate']} important={row['important_retention_rate']} "
                  f"pin_denials={row['pin_budget_denials']} insertion_refusals={row['protected_insertion_refusals']}")
    print("report:",path)

if __name__=="__main__":
    main()
