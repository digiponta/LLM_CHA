"""Side-by-side contrast operator evaluation; no training or chat mutation."""
import argparse,json
from pathlib import Path
from multi_axis_emotion_v09741 import detect_multi
from contrast_priority_emotion_v09742 import detect_priority,safe_response

CASES=[
"嬉しいけれど悲しい","悲しいけれど嬉しい",
"楽しかったけど疲れた","悲しくない。むしろ嬉しい。",
"悲しいけれど、どうすればいい？","嬉しいでも悲しい",
"悲しくない","悲しくないし、不安ではない",
"嬉しいけれど悲しいけれど嬉しい","量子力学について教えて",
]
def evaluate(cases=CASES):
    rows=[]
    for text in cases:
        old=detect_multi(text);new=detect_priority(text)
        rows.append({"input":text,"multi_axis_v09741":old.snapshot() if old else None,
                     "priority_v09742":new.snapshot() if new else None,
                     "suggested_response":safe_response(new)})
    return {"status":"DIAGNOSTIC_ONLY","count":len(rows),"rows":rows,
            "train_ready":False,"auto_promote":False,
            "limitations":"Heuristic Japanese contrast rules; +0.25/-0.25 represent design conventions, not measured affect. No live route changed."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/contrast_priority_v09742.json")
    a=p.parse_args()
    path=Path(a.output)
    if path.exists():raise FileExistsError(str(path))
    data=evaluate()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
