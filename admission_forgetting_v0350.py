"""LLM_CHA v0.3.5: explicit admission/forgetting decisions, holdout evaluation.

A metadata-only simulator. Evicted topics are never silently reconstructed;
a 'query' observes the present cache only. Never modifies Truth Gate or facts.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from adaptive_retention_eval_v023351 import Event
from auto_pin_protection_v0330 import evaluate as baseline

@dataclass
class Slot:
    last:int
    accesses:int=1
    explicit:bool=False
    auto:bool=False

def evaluate(events,capacity=4,auto_budget=None,explicit_topics=(),age_threshold=8):
    if type(capacity) is not int or not 1<=capacity<=16:
        raise ValueError("capacity")
    if auto_budget is None:
        auto_budget=capacity//2
    if type(auto_budget) is not int or not 0<=auto_budget<capacity:
        raise ValueError("auto_budget")
    if type(age_threshold) is not int or age_threshold<1:
        raise ValueError("age_threshold")
    if isinstance(explicit_topics,str):
        raise ValueError("explicit_topics")
    explicit=set(explicit_topics)
    if len(explicit)>capacity or any(not isinstance(x,str) or not x for x in explicit):
        raise ValueError("explicit_topics")
    active={}
    seen={}
    hits=queries=important_hits=important_queries=0
    admissions=rejections=evictions=auto_demotions=auto_promotions=0
    for turn,e in enumerate(events,1):
        if not isinstance(e,Event) or e.kind not in ("observe","query") or not isinstance(e.topic,str) or not e.topic.strip():
            raise ValueError("event")
        key=e.topic
        if e.kind=="query":
            queries+=1
            hit=key in active
            hits+=int(hit)
            if e.important:
                important_queries+=1
                important_hits+=int(hit)
            continue
        seen[key]=seen.get(key,0)+1
        if key in active:
            item=active[key]
            item.last=turn
            item.accesses=seen[key]
        else:
            if len(active)==capacity:
                eligible=[(k,s) for k,s in active.items() if not s.explicit and not s.auto]
                if not eligible:
                    # Fail closed: explicit and auto protected state is not
                    # rewritten to make room for a new topic.
                    rejections+=1
                    continue
                victim=min(eligible,key=lambda kv:(kv[1].accesses,kv[1].last,kv[0]))[0]
                del active[victim]
                evictions+=1
            item=Slot(turn,seen[key],explicit=key in explicit)
            active[key]=item
            admissions+=1
        if not e.important or item.explicit or item.auto:
            continue
        auto_names=[k for k,s in active.items() if s.auto]
        slots=min(auto_budget,capacity-sum(s.explicit for s in active.values()))
        if len(auto_names)<slots:
            item.auto=True
            auto_promotions+=1
        else:
            stale=[k for k in auto_names if turn-active[k].last>=age_threshold]
            if stale:
                victim=min(stale,key=lambda k:(active[k].accesses,active[k].last,k))
                if item.accesses>=active[victim].accesses:
                    active[victim].auto=False
                    item.auto=True
                    auto_demotions+=1
                    auto_promotions+=1
    total=admissions+rejections
    return {"policy":"admission_forgetting_v035","capacity":capacity,
            "queries":queries,"query_hits":hits,
            "return_success_rate":hits/queries if queries else None,
            "important_queries":important_queries,
            "important_retention_rate":important_hits/important_queries if important_queries else None,
            "admissions":admissions,"admission_rejections":rejections,
            "admission_rate":admissions/total if total else None,
            "evictions":evictions,"auto_promotions":auto_promotions,
            "auto_demotions":auto_demotions,
            "explicit_pins":sorted(k for k,s in active.items() if s.explicit),
            "auto_pins":sorted(k for k,s in active.items() if s.auto),
            "final_topics":sorted(active),"capacity_compliant":len(active)<=capacity,
            "budget_compliant":sum(s.auto for s in active.values())<=auto_budget}

def holdout_traces():
    # Frozen fixtures; do not choose thresholds based on these outcomes.
    O=lambda name,important=False: Event("observe",name,important)
    Q=lambda name,important=True: Event("query",name,important)
    return {
        "old_important_new_burst":[O("基礎A",True),O("基礎B",True)]
            +[O(f"未知{i}",True) for i in range(9)]
            +[Q("基礎A"),Q("基礎B"),Q("未知8")],
        "explicit_vs_unknown":[O("固定",True),O("一般",True)]
            +[O(f"未知{i}") for i in range(12)]
            +[Q("固定"),Q("一般"),Q("未知11")],
        "long_gap_revisit":[O("物理",True)]+[O(f"別{i}") for i in range(24)]
            +[Q("物理"),O("物理",True),Q("物理")],
        "frequent_old_topic":[O("CPU",True)]*6+[O("GPU",True)]
            +[O(f"補助{i}",True) for i in range(10)]
            +[Q("CPU"),Q("GPU"),Q("補助9")],
    }

def compare():
    rows=[]
    for scenario,events in holdout_traces().items():
        for capacity in (2,4,8):
            explicit=("固定",) if scenario=="explicit_vs_unknown" else ()
            for label,fn in (("v033",baseline),("v035",evaluate)):
                opts={"explicit_topics":explicit}
                if label=="v033":
                    opts["min_age_for_reallocation"]=8
                else:
                    opts["age_threshold"]=8
                outcome=fn(events,capacity,**opts)
                rows.append({"scenario":scenario,"version":label,**outcome})
    return {"version":"v0.3.5","holdout_scenarios":len(holdout_traces()),
            "rows":rows,"note":"synthetic holdout scenarios; no real conversation or semantic correctness evaluation"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--report",default="results/admission_forgetting_v0350.json")
    args=p.parse_args()
    result=compare()
    file=Path(args.report)
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("v0.3.5 holdout_scenarios=",result["holdout_scenarios"],"rows=",len(result["rows"]))
    for row in result["rows"]:
        print(row["scenario"],row["version"],"capacity=",row["capacity"],
              "return=",row["return_success_rate"],
              "important=",row["important_retention_rate"],
              "admission_rate=",row.get("admission_rate"),
              "rejections=",row.get("admission_rejections",row.get("protected_insertion_refusals")))
    print("report:",file)

if __name__=="__main__":
    main()
