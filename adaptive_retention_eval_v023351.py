"""v0.2.35.1 deterministic, trace-based retention policy comparison.

No mutation of user data, Semantic Memory or Truth State. All policies receive
identical observation streams. A query measures whether topic is retained
BEFORE any attempted retrieval, so a miss cannot become a hit by observation.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

POLICIES=("lru","frequency","pin_adaptive")

@dataclass(frozen=True)
class Event:
    kind: str
    topic: str
    important: bool=False

def simulate(events: list[Event], policy: str, capacity: int=4)->dict:
    if policy not in POLICIES or not 1<=capacity<=16:
        raise ValueError("invalid policy or capacity")
    present:dict[str,dict]={}
    hits=misses=important_hits=important_queries=evictions=protected_lost=0
    step=0
    for event in events:
        if event.kind not in {"observe","query"} or not event.topic:
            raise ValueError("invalid event")
        step+=1
        if event.kind=="query":
            hit=event.topic in present
            hits+=int(hit);misses+=int(not hit)
            if event.important:
                important_queries+=1;important_hits+=int(hit)
            # Queries are observational; no implicit re-insertion.
            continue
        if event.topic in present:
            row=present[event.topic]
            row["last"]=step;row["count"]+=1
            row["pin"]=row["pin"] or (policy=="pin_adaptive" and event.important)
            continue
        if len(present)>=capacity:
            candidates=[(topic,row) for topic,row in present.items()
                        if not (policy=="pin_adaptive" and row["pin"])]
            if not candidates:
                # Bounded conservative refusal. Record no insertion.
                protected_lost+=int(event.important)
                continue
            if policy=="frequency":
                victim=min(candidates,key=lambda p:(p[1]["count"],p[1]["last"],p[0]))[0]
            else:
                victim=min(candidates,key=lambda p:(p[1]["last"],p[1]["count"],p[0]))[0]
            evictions+=1
            del present[victim]
        present[event.topic]={"last":step,"count":1,
                              "pin":policy=="pin_adaptive" and event.important}
    total=hits+misses
    return {"policy":policy,"capacity":capacity,"queries":total,
            "query_hits":hits,"return_success_rate":hits/total if total else None,
            "important_queries":important_queries,"important_retention_rate":
              important_hits/important_queries if important_queries else None,
            "evictions":evictions,"protected_insertion_refusals":protected_lost,
            "final_topics":sorted(present),"capacity_compliant":len(present)<=capacity}

def fixture()->list[Event]:
    # Repeated core interests surrounded by one-off topic churn.
    out=[Event("observe","宇宙",True),Event("observe","GPU",True),
         Event("observe","数学"),Event("observe","文学")]
    for i in range(12):
        out.extend([Event("observe",f"一時話題{i}"),
                    Event("query","宇宙",True),Event("query","GPU",True),
                    Event("query","数学"),Event("observe","GPU",True)])
    return out

def compare(events:list[Event],capacity:int=4)->dict:
    runs=[simulate(events,p,capacity) for p in POLICIES]
    return {"version":"v0.2.35.1","events":len(events),"capacity":capacity,
            "policies":runs}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--capacity",type=int,default=4)
    p.add_argument("--report",default="results/adaptive_retention_v023351.json")
    args=p.parse_args()
    result=compare(fixture(),args.capacity)
    output=Path(args.report)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("report:",output)

if __name__=="__main__":
    main()
