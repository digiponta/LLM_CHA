"""Evaluate semantic-vector purpose prediction against rule baselines.

The already-seen v0.2.31.3 set is development data, not a final holdout.
A fresh prospective set is evaluated but small and hand-authored.
"""
import argparse,json
from pathlib import Path
from collections import defaultdict
from semantic_purpose_estimator_v02314 import SemanticPurposeEstimator
from purpose_confidence_v02311 import DSS,respond as baseline
from semantic_intent_normalizer_v02313 import respond as normalized
from prepare_purpose_generalization_v02312 import fixture as seen
from purpose_fresh_holdout_v02313 import fixture as previous

NEW=[
 ("pros-learn-1","LLMの原理を身につけたい","learning"),
 ("pros-learn-2","Pythonの文法を覚えたい","learning"),
 ("pros-learn-3","画像認識を勉強中です","learning"),
 ("pros-dev-1","小さなソフトを制作したい","development"),
 ("pros-dev-2","Pythonで便利な道具を組みたい","development"),
 ("pros-dev-3","LLMのコードを新しく書こうと思う","development"),
 ("pros-error-1","アプリが立ち上がらず困っています","troubleshooting"),
 ("pros-error-2","Pythonが急に停止する","troubleshooting"),
 ("pros-error-3","モデルの挙動が変です","troubleshooting"),
 ("pros-chat-1","今日はAIの話でもしようか","casual"),
 ("pros-chat-2","軽いおしゃべりに付き合って","casual"),
 ("pros-chat-3","ちょっと会話を楽しみたい","casual"),
 ("pros-amb-1","Pythonに少し興味が出てきた",None),
 ("pros-amb-2","LLMを一度触ってみようかな",None),
 ("pros-amb-3","画像認識を試そうか迷っている",None),
]
def fresh_cases():
    return [{"id":i,"text":text,"expected_purpose":purpose} for i,text,purpose in NEW]
def prediction(kind,estimator,text,threshold,margin):
    if kind=="semantic":
        v=estimator.predict(text,threshold,margin)
        return v["purpose"],v
    if kind=="baseline":
        d,action,_=baseline(DSS(),text)
    else:
        d,action,_,_=normalized(DSS(),text)
    return (d.purpose if action in ("HANDOFF","RESPOND") else None),{"action":action}
def evaluate(rows,kind,estimator,threshold,margin):
    out=[]
    for case in rows:
        purpose,details=prediction(kind,estimator,case["text"],threshold,margin)
        # For rules, purpose=None may be DISCOVERING rather than CONFIRMING;
        # this endpoint measures purpose acceptance, not dialogue action.
        correct=purpose==case["expected_purpose"]
        out.append({**case,"predicted_purpose":purpose,"correct":correct,
                    "details":details})
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--threshold",type=float,default=0.25)
    p.add_argument("--margin",type=float,default=0.04)
    p.add_argument("--out",default="results/semantic_purpose_v02314.json")
    a=p.parse_args()
    estimator=SemanticPurposeEstimator()
    splits={"previously_seen_v02312":seen(),
            "previously_seen_v02313":previous(),
            "prospective_v02314":fresh_cases()}
    report={"settings":{"threshold":a.threshold,"margin":a.margin},
            "method":"char_ngrams_TFIDF_nearest_exemplar_no_LLM_SEM"}
    for split,rows in splits.items():
        for kind in ("baseline","normalized","semantic"):
            result=evaluate(rows,kind,estimator,a.threshold,a.margin)
            ok=sum(r["correct"] for r in result)
            report[split+"/"+kind]={"correct":ok,"total":len(result),"rows":result}
            print(f"{split}/{kind}: {ok}/{len(result)}")
            for r in result:
                if not r["correct"]:
                    print(f'  FAIL {r["id"]}: expected={r["expected_purpose"]} predicted={r["predicted_purpose"]}')
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",out)
if __name__=="__main__":main()
