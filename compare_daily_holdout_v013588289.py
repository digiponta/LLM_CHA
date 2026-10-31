"""Complete, human-reviewable 2-vs-4 epoch daily conversation comparison.

Does not run chat, edit checkpoints or automatically assess semantic correctness.
"""
import argparse,json
from pathlib import Path
from daily_conversation_eval_v013588283 import evaluate

def compare(dataset,observations2,observations4):
    r2=evaluate(dataset,observations2)
    r4=evaluate(dataset,observations4)
    ids={x["id"] for x in dataset["cases"]}
    review={}
    for tag,obs in (("two",observations2),("four",observations4)):
        review[tag]={x["id"]:x for x in obs.get("runs",[])}
    rows=[]
    for case in dataset["cases"]:
        key=case["id"]
        row={"id":key,"question":case["question"]}
        for tag in ("two","four"):
            item=review[tag].get(key)
            row[tag]={"status":"NOT_RUN"} if item is None else {
                "status":"OBSERVED",
                "display":item.get("display",""),
                "candidate":item.get("candidate",""),
                "route":item.get("route",""),
                "human_appropriate":item.get("human_appropriate",None)}
        rows.append(row)
    complete=(r2["observed"]==len(ids) and r4["observed"]==len(ids))
    # A user rating is required for each answer. Never infer naturalness from surface checks.
    human_complete=complete and all(
        row[tag]["human_appropriate"] in (True,False)
        for row in rows for tag in ("two","four"))
    return {"status":"READY_FOR_HUMAN_REVIEW" if complete and not human_complete else
            "COMPLETE" if human_complete else "INCOMPLETE",
            "evaluation_only":True,
            "semantic_independence_verified":False,
            "human_naturalness_verified":bool(human_complete),
            "two":{"observed":r2["observed"],"surface_usable":r2["surface_usable"]},
            "four":{"observed":r4["observed"],"surface_usable":r4["surface_usable"]},
            "rows":rows}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--dataset",default="data/daily_conversation_eval_v013588283.json")
    a.add_argument("--two",required=True)
    a.add_argument("--four",required=True)
    a.add_argument("--output",default="results/daily_holdout_ab_v013588289.json")
    x=a.parse_args()
    def load(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    result=compare(load(x.dataset),load(x.two),load(x.four))
    out=Path(x.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
