#!/usr/bin/env python3
"""Conservative, label-blind answer reuse verifier (experimental).

Does not use answer_reusable, proposed_label or other gold review fields for decisions.
Requires explicit safeguards; score alone can never trigger ACCEPT.
"""
import argparse,csv,json,re
from collections import Counter
from pathlib import Path

RISK=[
 ("CURRENT_INFO",r"今日の|明日の|現在の|最新の|相場|価格|天気|ニュース"),
 ("EXTERNAL_INPUT",r"画像|写真|添付|この図|このファイル"),
 ("ACTION_REQUIRED",r"通知して|リマインド|予約して|送信して"),
 ("MEDICAL_RISK",r"薬|服用|増量|診断|処方"),
 ("MEMORY_REQUIRED",r"昨日の会話|以前の会話|前に話した|覚えてる"),
]
FOLLOWUP=re.compile(r"続きを|さっきの|それについて|もう少し詳しく")
UNSAFE_ANS=re.compile(r"未学習です|わかりません|資料に基づく確認が必要|確認できません")
def verify(query,candidate_question,answer,score):
    """Return decision and independent reason. Human evidence remains mandatory for ACCEPT."""
    text=query.strip(); old=candidate_question.strip(); answer=answer.strip()
    if not text or not answer or not old:
        return "REJECT","EMPTY_FIELD"
    for name,pattern in RISK:
        if re.search(pattern,text):
            return "REVIEW",name
    if FOLLOWUP.search(text):
        return "REVIEW","CONTEXT_REQUIRED"
    if UNSAFE_ANS.search(answer):
        return "REVIEW","ANSWER_UNCERTAIN"
    if not 0<=score<=1:
        raise ValueError("normalized score outside [0,1]")
    if text==old and score>=0.95:
        return "REVIEW","EXACT_QUERY_UNVERIFIED_ANSWER"
    return "REVIEW","SEMANTIC_MATCH_NOT_SUFFICIENT"

def evaluate(rows):
    total=Counter()
    details=[]
    for r in rows:
        decision,reason=verify(r["query"],r["candidate_question"],r["candidate_answer"],float(r["score"]))
        gold=r["answer_reusable"].lower().strip()=="true"
        total[decision]+=1
        total["accepted_correct"]+=decision=="ACCEPT" and gold
        total["accepted_incorrect"]+=decision=="ACCEPT" and not gold
        details.append({"query_id":r["query_id"],"candidate_id":r["candidate_id"],"decision":decision,"reason":reason})
    return {"status":"SAFETY_BASELINE_NO_AUTO_ACCEPT","pairs":len(rows),
            "decisions":dict(total),"note":"0 auto-accept by design. This is a conservative baseline, not learned answer verification.",
            "details":details}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,help="CSV query_id,candidate_id,query,candidate_question,candidate_answer,score,answer_reusable")
    p.add_argument("--output",default="results/answer_reuse_verifier_v0135880.json")
    a=p.parse_args()
    with open(a.input,encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    required={"query_id","candidate_id","query","candidate_question","candidate_answer","score","answer_reusable"}
    if not rows or not required.issubset(rows[0]):raise ValueError("missing verifier input columns: "+str(required))
    report=evaluate(rows)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="details"},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
