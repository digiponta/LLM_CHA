"""Replay prior saved generation through Japanese repair and semantic recheck."""
import argparse,json
from pathlib import Path
from collections import Counter
from japanese_repair_gate_v09745 import repair_and_recheck
def evaluate(data):
    rows=[]
    for record in data["rows"]:
        result=repair_and_recheck(record["input"],record["combined_sft_generated"])
        rows.append({"input":record["input"],"result":result.snapshot()})
    return {"status":"DIAGNOSTIC_ONLY","cases":len(rows),
            "decisions":dict(Counter(r["result"]["decision"] for r in rows)),
            "rows":rows,"train_ready":False,"auto_promote":False,
            "limitations":"Only reviewed exact pattern is repaired. REVIEW/ABSTAIN is not an approval; no model training."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/emotion_response_plan_v09743.json")
    p.add_argument("--output",default="results/japanese_repair_gate_v09745.json")
    a=p.parse_args()
    inp=Path(a.input);out=Path(a.output)
    if inp.resolve()==out.resolve() or out.exists():raise ValueError("output collision or exists")
    result=evaluate(json.loads(inp.read_text(encoding="utf-8")))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
