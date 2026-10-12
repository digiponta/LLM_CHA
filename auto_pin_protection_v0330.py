"""v0.3.3: two-stage auto-pin protection and explicit reallocation.

Important signals are fixture labels, not verified facts. No chat integration.
Unlike v0.3.2, active auto-pins are never eligible for ordinary eviction.
When all evictable space is occupied, an incoming important topic may compete
for an auto-pin slot by priority; otherwise it remains a normal topic.
"""
from dataclasses import dataclass
from adaptive_retention_eval_v023351 import Event
from retention_cross_scenario_v0300 import scenarios
from hybrid_retention_v0310 import hybrid
from adaptive_importance_v0320 import evaluate as previous

@dataclass
class State:
    last:int
    count:int
    explicit:bool=False
    auto:bool=False

def evaluate(events,capacity=4,auto_budget=None,explicit_topics=(),
             min_age_for_reallocation=8):
    if type(capacity) is not int or not 1<=capacity<=16:
        raise ValueError("capacity")
    if auto_budget is None:
        auto_budget=max(0,capacity//2)
    if type(auto_budget) is not int or not 0<=auto_budget<capacity:
        raise ValueError("auto_budget must reserve >=1 non-auto slot")
    if type(min_age_for_reallocation) is not int or min_age_for_reallocation<1:
        raise ValueError("min_age_for_reallocation")
    if isinstance(explicit_topics,str):
        raise ValueError("explicit_topics")
    protected=set(explicit_topics)
    if len(protected)>capacity or any(not isinstance(s,str) or not s for s in protected):
        raise ValueError("explicit_topics")
    cache={}
    observed={}
    hits=queries=important_hits=important_queries=evictions=refusals=promotions=demotions=0
    for turn,e in enumerate(events,1):
        if not isinstance(e,Event) or e.kind not in ("observe","query") or not isinstance(e.topic,str) or not e.topic:
            raise ValueError("event")
        key=e.topic
        if e.kind=="query":
            queries+=1
            found=key in cache
            hits+=int(found)
            if e.important:
                important_queries+=1
                important_hits+=int(found)
            continue
        observed[key]=observed.get(key,0)+1
        if key in cache:
            entry=cache[key]
            entry.last=turn
            entry.count=observed[key]
        else:
            if len(cache)==capacity:
                unprotected=[(k,v) for k,v in cache.items() if not v.explicit and not v.auto]
                if not unprotected:
                    refusals+=1
                    continue
                victim=min(unprotected,key=lambda kv:(kv[1].count,kv[1].last,kv[0]))[0]
                del cache[victim]
                evictions+=1
            entry=State(turn,observed[key],key in protected)
            cache[key]=entry
        # Promotion/reallocation only following an explicit important signal.
        if not e.important or entry.explicit or entry.auto:
            continue
        auto_names=[k for k,v in cache.items() if v.auto]
        slots=max(0,min(auto_budget,capacity-sum(v.explicit for v in cache.values())))
        if len(auto_names)<slots:
            entry.auto=True
            promotions+=1
        elif auto_names:
            # Reallocation is restricted to stale auto pins; never demote a
            # recently accessed auto pin or explicit protection.
            stale=[k for k in auto_names
                   if turn-cache[k].last>=min_age_for_reallocation]
            if stale:
                victim=min(stale,key=lambda k:(cache[k].count,cache[k].last,k))
                # Priority rule: a new important topic is eligible to replace
                # a stale pin only when its observed count is at least victim's.
                if entry.count>=cache[victim].count:
                    cache[victim].auto=False
                    entry.auto=True
                    demotions+=1
                    promotions+=1
    return {"policy":"protected_auto_pin_v033","capacity":capacity,"auto_budget":auto_budget,
            "queries":queries,"query_hits":hits,
            "return_success_rate":hits/queries if queries else None,
            "important_queries":important_queries,
            "important_retention_rate":important_hits/important_queries if important_queries else None,
            "evictions":evictions,"auto_promotions":promotions,"auto_demotions":demotions,
            "protected_insertion_refusals":refusals,
            "explicit_pins":sorted(k for k,v in cache.items() if v.explicit),
            "auto_pins":sorted(k for k,v in cache.items() if v.auto),
            "final_topics":sorted(cache),
            "capacity_compliant":len(cache)<=capacity,
            "budget_compliant":sum(v.auto for v in cache.values())<=auto_budget}

def compare():
    rows=[]
    for scenario,events in scenarios().items():
        for cap in (2,4,8):
            for method in (hybrid,previous,evaluate):
                rows.append({"scenario":scenario,**method(events,cap)})
    return {"version":"v0.3.3","rows":rows}

if __name__=="__main__":
    import json
    from pathlib import Path
    p=Path("results/auto_pin_protection_v0330.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    report=compare()
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for row in report["rows"]:
        if row["policy"]=="protected_auto_pin_v033":
            print(row["scenario"],"capacity=",row["capacity"],
                  "return=",row["return_success_rate"],
                  "important=",row["important_retention_rate"],
                  "demotions=",row["auto_demotions"])
    print("report:",p)
