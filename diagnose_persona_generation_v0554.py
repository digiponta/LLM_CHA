"""v0.5.54 deterministic raw-generation diagnostics, no quality claims from heuristics."""
import argparse,json,re
from pathlib import Path

def diagnose(text,user):
    t=text.strip()
    fragments=not t or len(t)<8 or t.startswith(("、","。","の前身","を参照"))
    parts=[p.strip() for p in re.split(r"[、。！？!?\s]+",t) if p.strip()]
    repeated=[p for p in set(parts) if len(p)>=2 and parts.count(p)>=3]
    nums=re.findall(r"\d+",t)
    numerical_loop=len(nums)>=5 and len(set(nums))<=max(2,len(nums)//3)
    # Character overlap is only a weak proxy. No semantic relevance inference.
    def bigrams(s):
        s=re.sub(r"[\s。、！？!?]+","",s)
        return {s[i:i+2] for i in range(len(s)-1)}
    a,b=bigrams(user),bigrams(t)
    overlap=round(len(a&b)/len(a),4) if a else None
    return {"fragment_flag":fragments,"repeated_phrase_flag":bool(repeated),
            "numerical_loop_flag":numerical_loop,
            "input_bigram_recall_proxy":overlap,
            "response_chars":len(t),"manual_quality_label":None}

def analyze(data):
    rows=[]
    for row in data["rows"]:
        raw=row["raw_llm"]["reply"]
        d=diagnose(raw,row["user"])
        rows.append({"scenario":row["scenario"],"turn":row["turn"],
            "user":row["user"],"raw_reply":raw,**d})
    n=len(rows)
    flags=("fragment_flag","repeated_phrase_flag","numerical_loop_flag")
    return {"version":"v0.5.54","source":"RECORDED_RAW_GENERATION",
      "samples":n,"flag_counts":{k:sum(bool(r[k]) for r in rows) for k in flags},
      "flag_rates":{k:(round(sum(bool(r[k]) for r in rows)/n,4) if n else None) for k in flags},
      "bigram_overlap_mean":(round(sum(r["input_bigram_recall_proxy"] or 0 for r in rows)/n,4) if n else None),
      "topic_relevance_accuracy":None,"persona_accuracy":None,
      "semantic_correctness":None,"human_quality_accuracy":None,
      "heuristics_are_not_ground_truth":True,
      "training_recommended_automatically":False,"rows":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/persona_ablation_v0552.json")
    p.add_argument("--output",default="results/persona_generation_quality_v0554.json")
    a=p.parse_args()
    report=analyze(json.loads(Path(a.input).read_text(encoding="utf-8")))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False,indent=2))
    print("output:",path)
if __name__=="__main__":main()
