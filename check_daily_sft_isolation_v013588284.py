"""Verify daily training pairs do not exactly copy holdout prompts/answers.

Exact-match only; semantic overlap still requires human review.
"""
import argparse,json,re
from pathlib import Path

def normalize(s):
    return re.sub(r"[\s。？！?!、，,.！]", "", str(s)).strip()
def check(train,holdout):
    rows=[json.loads(x) for x in Path(train).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    cases=json.loads(Path(holdout).read_text(encoding="utf-8-sig"))["cases"]
    questions={normalize(x["question"]) for x in cases}
    examples={normalize(x.get("example_acceptable","")) for x in cases}
    seen=set()
    issues=[]
    for i,row in enumerate(rows,1):
        q=normalize(row.get("user",""))
        a=normalize(row.get("assistant",""))
        if not q or not a:issues.append([i,"EMPTY_PAIR"])
        if q in questions:issues.append([i,"EXACT_HOLDOUT_QUESTION"])
        if a in examples:issues.append([i,"EXACT_HOLDOUT_ANSWER"])
        if q in seen:issues.append([i,"DUPLICATE_PROMPT"])
        if row.get("source")!="chat-manual":issues.append([i,"UNTRUSTED_SOURCE"])
        seen.add(q)
    return {"status":"PASS" if not issues else "BLOCKED","training_pairs":len(rows),
            "holdout_questions":len(cases),"issues":issues,
            "semantic_independence_verified":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/daily_sft_train_v013588284.jsonl")
    p.add_argument("--holdout",default="data/daily_conversation_eval_v013588283.json")
    a=p.parse_args();report=check(a.train,a.holdout)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["issues"]:raise SystemExit(2)
if __name__=="__main__":main()
