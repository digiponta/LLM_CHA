"""Side-by-side continuous and multi-axis semantic diagnostics."""
import argparse,json
from pathlib import Path
from continuous_emotion_semantics_v09740 import detect_affect
from multi_axis_emotion_v09741 import detect_multi,safe_response

CASES=[
"悲しくないよ","寂しくないよ","嬉しくない","楽しくなかった",
"不安ではない","怒っていない","悲しくない。むしろ嬉しい。",
"嬉しいけれど悲しい","楽しかったけど疲れた",
"悲しくないし、不安ではない","今日は楽しかった",
"量子力学について教えて",
]
def evaluate(cases=CASES):
    rows=[]
    for text in cases:
        old=detect_affect(text)
        current=detect_multi(text)
        rows.append({"input":text,"continuous_v09740":old.snapshot() if old else None,
                     "multi_axis_v09741":current.snapshot() if current else None,
                     "safe_response":safe_response(current)})
    return {"status":"DIAGNOSTIC_ONLY","count":len(rows),
            "multi_axis_detected":sum(x["multi_axis_v09741"] is not None for x in rows),
            "rows":rows,"train_ready":False,"auto_promote":False,
            "note":"Symbolic values are uncalibrated design constants; no model weights or chat behavior altered."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/multi_axis_emotion_v09741.json")
    a=p.parse_args();path=Path(a.output)
    if path.exists():raise FileExistsError(str(path))
    report=evaluate()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
