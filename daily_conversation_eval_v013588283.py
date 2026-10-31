"""Offline evaluator of user-recorded chat outputs; never claims to execute the model.

Input observations JSON: {"runs":[{"id":"daily-001","candidate":"...", "display":"...", "route":"..."}]}
"""
import argparse,json,re
from pathlib import Path

BAD_PREFIX=re.compile(r"^[。．.!！?？、，,;；]")
def grade(candidate,display,route):
    candidate=str(candidate or "").strip()
    display=str(display or "").strip()
    malformed=not candidate or bool(BAD_PREFIX.match(candidate))
    fallback=display=="未学習です"
    # Surface checks, NOT semantic naturalness or human equivalence.
    usable=bool(display) and not bool(BAD_PREFIX.match(display)) and not fallback
    return {"candidate_malformed":malformed,"fallback":fallback,
            "display_surface_usable":usable,"needs_human_review":usable,
            "route":str(route or "UNKNOWN")}
def evaluate(dataset,observations):
    cases=dataset["cases"]
    by_id={}
    for item in observations.get("runs",[]):
        id=item.get("id")
        if id in by_id:raise ValueError("DUPLICATE_CASE_ID:"+str(id))
        by_id[id]=item
    known={c["id"] for c in cases}
    if set(by_id)-known:raise ValueError("UNKNOWN_CASE_ID")
    rows=[]
    for case in cases:
        item=by_id.get(case["id"])
        if item is None:
            rows.append({"id":case["id"],"question":case["question"],"status":"NOT_RUN"})
            continue
        score=grade(item.get("candidate",""),item.get("display",""),item.get("route",""))
        rows.append({"id":case["id"],"question":case["question"],"status":"OBSERVED",**score})
    observed=[x for x in rows if x["status"]=="OBSERVED"]
    return {"status":"DAILY_DIALOGUE_EVAL","observed":len(observed),"total":len(cases),
            "surface_usable":sum(x["display_surface_usable"] for x in observed),
            "candidate_malformed":sum(x["candidate_malformed"] for x in observed),
            "fallback":sum(x["fallback"] for x in observed),
            "human_naturalness_verified":False,"model_improvement_claimed":False,
            "rows":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",default="data/daily_conversation_eval_v013588283.json")
    p.add_argument("--observations",required=True)
    p.add_argument("--output",default="results/daily_conversation_eval_v013588283.json")
    a=p.parse_args()
    def load(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    report=evaluate(load(a.dataset),load(a.observations))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
