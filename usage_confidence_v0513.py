"""LLM_CHA v0.5.13: operational usage counters, distinct from truth."""
import json
import math
from pathlib import Path
from conversation_resource_memory_v042866 import write_json_atomic

def rows(path):
    p=Path(path)
    data=json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else []
    if not isinstance(data,list):
        raise ValueError("invalid candidates")
    return data

def get(path,number):
    data=rows(path)
    if type(number)!=int or number<1 or number>len(data):
        raise ValueError("invalid candidate ID")
    return data, data[number-1]

def summary(path,number):
    _,r=get(path,number)
    positive=r.get("positive_feedback",0)
    negative=r.get("negative_feedback",0)
    score=min(1.0,math.log1p(positive)/math.log1p(20))*math.exp(-1.5*negative)
    return dict(id=number,concept=r["concept"],usage_count=r.get("usage_count",0),
        positive_feedback=positive,negative_feedback=negative,
        usage_confidence=round(score,6),
        operational_status=r.get("operational_status","PROVISIONAL"),
        truth_state=r["truth_state"],verified=False,train_ready=False)

def update(path,number,action):
    if action not in ("used","positive","negative"):
        raise ValueError("invalid action")
    data,r=get(path,number)
    if r.get("truth_state")!="USER_REPORTED_UNVERIFIED":
        raise ValueError("unsupported truth state")
    field={"used":"usage_count","positive":"positive_feedback",
           "negative":"negative_feedback"}[action]
    r[field]=r.get(field,0)+1
    neg=r.get("negative_feedback",0)
    pos=r.get("positive_feedback",0)
    r["operational_status"]="CONTESTED" if neg else (
        "OPERATIONAL" if pos>=5 else "PROVISIONAL")
    r.update(verified=False,train_ready=False,approved_for_sleep=False,fact_promoted=False)
    write_json_atomic(data,path)
    return summary(path,number)
