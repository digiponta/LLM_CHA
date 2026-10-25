"""Replay v0.9.7.43 saved Combined-SFT responses through v0.9.7.44 gate."""
import argparse,json
from collections import Counter
from pathlib import Path
from semantic_response_gate_v09744 import assess
def evaluate(report):
    cases=report.get("rows",[])
    if not cases:raise ValueError("no rows")
    rows=[]
    for item in cases:
        result=assess(item["input"],item["combined_sft_generated"])
        rows.append({"input":item["input"],"gate":result.snapshot()})
    decisions=Counter(x["gate"]["decision"] for x in rows)
    return {"status":"DIAGNOSTIC_ONLY","cases":len(rows),"decisions":dict(decisions),
            "rows":rows,"train_ready":False,"auto_promote":False,
            "limitations":"Lexical-only; cannot guarantee semantic accuracy or fluency. Previously inspected development inputs."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/emotion_response_plan_v09743.json")
    p.add_argument("--output",default="results/semantic_response_gate_v09744.json")
    a=p.parse_args()
    source=Path(a.input);out=Path(a.output)
    if out.resolve()==source.resolve() or out.exists():raise ValueError("output collision or exists")
    result=evaluate(json.loads(source.read_text(encoding="utf-8")))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
