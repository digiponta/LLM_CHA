"""Compare old emotion decisions with continuous-axis semantic states."""
import argparse,json
from pathlib import Path
from continuous_emotion_semantics_v09740 import detect_affect,safe_response
from emotion_aware_dialogue_v09733 import detect
CASES=[
 "悲しくないよ","寂しくないよ","嬉しくない","楽しくなかった",
 "不安ではない","怒っていない","悲しくない。むしろ嬉しい。",
 "嬉しいけれど悲しい","楽しかったけど疲れた","今日は楽しかった",
 "悲しくないし、不安ではない","量子力学について教えて",
]
def evaluate(cases):
    rows=[]
    for text in cases:
        old=detect(text);new=detect_affect(text)
        rows.append({"input":text,
          "existing":old.snapshot() if old else None,
          "continuous":new.snapshot() if new else None,
          "suggested_response":safe_response(new),
          "diagnostic_only":True})
    return {"status":"DIAGNOSTIC_ONLY","cases":len(rows),"rows":rows,
      "warnings":["A fixed +0.25 or -0.25 is a design convention, not a measured emotion score.",
                  "Unknown/compound input may abstain; current chat route unchanged.",
                  "State reflects text, not a verified mental state."],
      "train_ready":False,"auto_promote":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/continuous_emotion_v09740.json")
    a=p.parse_args()
    out=Path(a.output)
    if out.exists():raise FileExistsError(str(out))
    data=evaluate(CASES)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
