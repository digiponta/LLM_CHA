"""Conservative response-quality diagnostics for v0.9.7.38 factorial outputs.

This is a transparent rule-based rubric, NOT a semantic oracle. Unknown
or ambiguous examples are marked REVIEW, not silently counted as PASS.
"""
import argparse,csv,json,re
from collections import defaultdict
from pathlib import Path

POS=("良かった","よかった","嬉しい","うれしい","楽しい","楽し","満足","おめでとう","気に入った")
NEG=("残念","がっかり","悲しい","つらい","辛い","寂しい","落ち込")
REST=("疲れ","お疲れ","休","無理しない","頑張った")
THANKS=("どういたしまして","役に立て","こちらこそ","言ってもらえて")
CLARIFY=("迷","悩","整理","選択肢","一緒に","どの","何が","どう")
BAD=("�","糖衣|","FTP@","~(Kenne")

def categories(emotion):
    if emotion in ("POSITIVE","ENJOYMENT","JOY"):return "positive"
    if emotion in ("NEGATED_POSITIVE","DISAPPOINTMENT"):return "disappointment"
    if emotion=="SADNESS":return "sadness"
    if emotion in ("NEGATED_SADNESS","NON_SADNESS"):return "negated_sadness"
    if emotion=="MIXED":return "mixed"
    if emotion=="FATIGUE":return "fatigue"
    if emotion=="GRATITUDE":return "gratitude"
    if emotion=="UNCERTAINTY":return "uncertainty"
    if emotion=="GREETING":return "greeting"
    if emotion=="IDENTITY":return "identity"
    return "unknown"

def quality(text,emotion):
    t=str(text or "").strip()
    group=categories(emotion)
    if not t or len(t)>100 or any(x in t for x in BAD):
        return {"verdict":"FAIL","reason":"malformed","group":group}
    if len(t)<4 or not re.search("[ぁ-んァ-ヶ一-龯]",t):
        return {"verdict":"FAIL","reason":"fragment-or-no-japanese","group":group}
    if group=="positive":
        if any(w in t for w in ("残念","悲しい","つらい","寂しい")):return {"verdict":"FAIL","reason":"positive-negative-contradiction","group":group}
        if any(w in t for w in POS):return {"verdict":"PASS","reason":"positive-cue","group":group}
    elif group=="disappointment":
        if "おめでとう" in t:return {"verdict":"FAIL","reason":"disappointment-congratulated","group":group}
        if any(w in t for w in ("残念","がっかり","期待外れ","楽しくなかった")):
            return {"verdict":"PASS","reason":"disappointment-cue","group":group}
    elif group=="sadness":
        if "おめでとう" in t:return {"verdict":"FAIL","reason":"sadness-congratulated","group":group}
        if any(w in t for w in ("悲しい","つらい","辛い","寂しい","切ない","気分が沈")):
            return {"verdict":"PASS","reason":"sadness-cue","group":group}
    elif group=="negated_sadness":
        if any(w in t for w in ("悲しくない","悲しいわけではない","寂しくない","寂しくはない","悲しいということではない")):
            return {"verdict":"PASS","reason":"explicit-negation-preserved","group":group}
        if any(w in t for w in ("悲しいんだね","寂しいんだね","悲しかったね","それは残念")):
            return {"verdict":"FAIL","reason":"negation-reversed","group":group}
    elif group=="mixed":
        # Conservative: require both positive and negative/fatigue cues.
        has_positive=any(w in t for w in POS)
        has_other=any(w in t for w in ("悲しい","残念","後悔","疲れ","休","つらい"))
        if has_positive and has_other:return {"verdict":"PASS","reason":"two-affects-reflected","group":group}
        return {"verdict":"REVIEW","reason":"mixed-affects-not-demonstrated","group":group}
    elif group=="fatigue":
        if any(w in t for w in REST):return {"verdict":"PASS","reason":"fatigue-support","group":group}
    elif group=="gratitude":
        if any(w in t for w in ("残念","悲しい","つらい")):return {"verdict":"FAIL","reason":"gratitude-contradicted","group":group}
        if any(w in t for w in THANKS):return {"verdict":"PASS","reason":"gratitude-acknowledged","group":group}
    elif group=="uncertainty":
        if any(w in t for w in CLARIFY):return {"verdict":"PASS","reason":"clarification-or-options","group":group}
    elif group=="greeting":
        if any(w in t for w in ("こんにちは","おはよう","こんばんは")):return {"verdict":"PASS","reason":"greeting-returned","group":group}
    elif group=="identity":
        if "長門有希" in t:return {"verdict":"PASS","reason":"identity-preserved","group":group}
    return {"verdict":"REVIEW","reason":"insufficient-evidence","group":group}

ARMS=("plain","emotion","strategy","both")
def evaluate_report(report):
    rows=report.get("rows")
    if not isinstance(rows,list) or not rows:raise ValueError("Missing evaluation rows")
    detailed=[]
    by_arm={a:{"PASS":0,"FAIL":0,"REVIEW":0} for a in ARMS}
    by_group=defaultdict(lambda:{a:{"PASS":0,"FAIL":0,"REVIEW":0} for a in ARMS})
    for row in rows:
        if not all(a in row["outputs"] for a in ARMS):raise ValueError("missing arm")
        for arm in ARMS:
            q=quality(row["outputs"][arm]["text"],row["emotion"])
            by_arm[arm][q["verdict"]]+=1
            by_group[q["group"]][arm][q["verdict"]]+=1
            detailed.append({"id":row["id"],"input":row["input"],"emotion":row["emotion"],
                "arm":arm,"response":row["outputs"][arm]["text"],
                "verdict":q["verdict"],"reason":q["reason"],"manual_verdict":"",
                "manual_notes":""})
    return {"status":"DIAGNOSTIC_ONLY","total_cases":len(rows),
        "by_arm":by_arm,"by_group":dict(by_group),
        "limitations":"Lexical cues cannot establish empathy or Japanese fluency; REVIEW is not a failure or success. Manual blinded assessment required.",
        "train_ready":False,"auto_promote":False},detailed

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/emotion_factorial_v09738.json")
    p.add_argument("--output",default="results/emotion_quality_v09739.json")
    p.add_argument("--review-csv",default="results/emotion_quality_review_v09739.csv")
    a=p.parse_args()
    source=Path(a.input);out=Path(a.output);csvpath=Path(a.review_csv)
    if out.resolve()==source.resolve() or csvpath.resolve()==source.resolve() or out.resolve()==csvpath.resolve() or out.exists() or csvpath.exists():
        raise ValueError("Output path collision or already exists")
    report=json.loads(source.read_text(encoding="utf-8"))
    result,details=evaluate_report(report)
    out.parent.mkdir(parents=True,exist_ok=True)
    csvpath.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    with csvpath.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(details[0]))
        writer.writeheader();writer.writerows(details)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("review:",csvpath)
if __name__=="__main__":main()
