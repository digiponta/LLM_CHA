"""Reassess v0.5.52 real recorded rows without regenerating or changing originals."""
import argparse,json
from pathlib import Path
from persona_hybrid_safety_v0553 import decide

def replay(report):
    rows=report["rows"]
    out=[]
    for row in rows:
        checked=decide(row)
        out.append({"scenario":row["scenario"],"turn":row["turn"],
                    "original_hybrid":row["hybrid"]["selected"],
                    "gated_hybrid":checked,
                    "raw_reply":row["raw_llm"]["reply"]})
    counts={}
    for row in out:
        key=row["gated_hybrid"]["selected"]
        counts[key]=counts.get(key,0)+1
    return {"version":"v0.5.53","origin":"REPLAY_RECORDED_V0552",
            "total":len(out),"selection_counts":counts,
            "human_persona_assessment":None,"knowledge_truth_assessment":None,
            "auto_learning":False,"rows":out}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--input",default="results/persona_ablation_v0552.json")
    a.add_argument("--output",default="results/persona_hybrid_safety_v0553.json")
    args=a.parse_args()
    source=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result=replay(source)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
    print("output:",target)
if __name__=="__main__":main()
