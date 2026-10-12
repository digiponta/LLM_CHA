"""LLM_CHA v0.3.2 experimental importance-based auto-pin reallocation.

Explicit pins are never silently demoted. Auto pins can be reallocated inside
a bounded budget. This is a pure metadata simulation, NOT chat.py integration.
"""
from dataclasses import dataclass
from adaptive_retention_eval_v023351 import Event
from retention_cross_scenario_v0300 import scenarios
from hybrid_retention_v0310 import hybrid

@dataclass
class Item:
    last: int
    frequency: int
    explicit: bool=False
    auto: bool=False

def evaluate(events, capacity=4, auto_budget=None, explicit_topics=()):
    if type(capacity) is not int or not 1<=capacity<=16:
        raise ValueError("capacity")
    if auto_budget is None:
        auto_budget=max(0,capacity//2)
    if type(auto_budget) is not int or not 0<=auto_budget<=capacity:
        raise ValueError("auto_budget")
    explicit=set(explicit_topics)
    if len(explicit)>capacity or any(not isinstance(x,str) or not x for x in explicit):
        raise ValueError("explicit_topics")
    active={}
    lifetime={}
    hits=queries=important_hits=important_queries=0
    evictions=demotions=refusals=0
    def score(key,item,step):
        return (4*int(item.auto) + 2*min(item.frequency,8)
                - (step-item.last),item.last,key)
    for step,event in enumerate(events,1):
        if not isinstance(event,Event) or event.kind not in ("observe","query") or not isinstance(event.topic,str) or not event.topic:
            raise ValueError("event")
        key=event.topic
        if event.kind=="query":
            queries+=1
            hit=key in active
            hits+=int(hit)
            if event.important:
                important_queries+=1;important_hits+=int(hit)
            continue
        lifetime[key]=lifetime.get(key,0)+1
        if key in active:
            current=active[key]
            current.last=step
            current.frequency=lifetime[key]
        else:
            if len(active)>=capacity:
                eligible=[(name,item) for name,item in active.items() if not item.explicit]
                if not eligible:
                    refusals+=1
                    continue
                victim=min(eligible,key=lambda pair:score(pair[0],pair[1],step))[0]
                del active[victim]
                evictions+=1
            active[key]=Item(step,lifetime[key],explicit=(key in explicit))
        # Important signals can request auto-pinning, without overriding
        # explicit protections or the global auto-pin budget.
        if event.important and not active[key].explicit:
            active[key].auto=True
        autos=[(name,item) for name,item in active.items() if item.auto and not item.explicit]
        if len(autos)>auto_budget:
            to_demote=sorted(autos,key=lambda pair:(2*min(pair[1].frequency,8)
                                      -(step-pair[1].last),pair[1].last,pair[0]))
            for name,item in to_demote[:len(autos)-auto_budget]:
                item.auto=False
                demotions+=1
    return {"policy":"reallocated_auto_pin","capacity":capacity,"auto_budget":auto_budget,
            "queries":queries,"query_hits":hits,
            "return_success_rate":hits/queries if queries else None,
            "important_queries":important_queries,
            "important_retention_rate":important_hits/important_queries if important_queries else None,
            "evictions":evictions,"auto_demotions":demotions,
            "protected_insertion_refusals":refusals,
            "explicit_pins":sorted(k for k,x in active.items() if x.explicit),
            "auto_pins":sorted(k for k,x in active.items() if x.auto),
            "final_topics":sorted(active),
            "capacity_compliant":len(active)<=capacity,
            "budget_compliant":sum(x.auto for x in active.values())<=auto_budget}

def compare():
    rows=[]
    for name,events in scenarios().items():
        for capacity in (2,4,8):
            rows.append({"scenario":name,**hybrid(events,capacity)})
            rows.append({"scenario":name,**evaluate(events,capacity)})
    return {"version":"v0.3.2","rows":rows}
