"""Frozen parser: action + question quality comparisons on seen and prospective cases."""
import json,argparse
from pathlib import Path
from structured_purpose_holdout_v02316 import fixture as seen
from semantic_dialogue_policy_v02317 import decide as old
from structured_semantic_purpose_v02315 import extract
from evidence_dialogue_policy_v02318 import decide
NEW=[
 ("clear-build","Pythonで小さなツールを組み上げたい","HANDOFF"),
 ("clear-trouble","LLMの出力がおかしい","HANDOFF"),
 ("clear-learn","Pythonの使い方を学習したい","HANDOFF"),
 ("casual","画像認識の雑談をしたい","RESPOND"),
 ("multi","LLMを勉強して開発もしたい","PLAN"),
 ("seq","LLMを勉強してから開発したい","PLAN"),
 ("ambiguous","Pythonに興味がある","ASK_CONFIRMATION"),
 ("unresolved","LLMが気になっている","ASK_CONFIRMATION"),
 ("unknown","12345678","ASK_CLARIFICATION"),
 ("negation","Pythonは開発じゃなく勉強したい","HANDOFF"),
 ("unspecified","Pythonで何かしたい","ASK_CONFIRMATION"),
 ("clear-code","LLMを自作したい","HANDOFF"),
]
def evaluate(rows):
    result=[]
    for r in rows:
        s=extract(r["text"])
        before=old(s)
        after=decide(r["text"],s)
        action=after.action
        needs_question=action in ("ASK_CONFIRMATION","ASK_CLARIFICATION")
        question=after.question or ""
        question_ok=((not needs_question and not question) or
                     (needs_question and bool(question) and
                      not any(x in question for x in ("casual","learning","development","troubleshooting"))))
        result.append({"id":r["id"],"text":r["text"],"expected":r["action"],
                       "old_action":before.action,"new_action":action,
                       "old_correct":before.action==r["action"],
                       "new_correct":action==r["action"],
                       "question":question,"question_format_ok":question_ok,
                       "parser_status":s.status,"parser_purposes":s.purposes,
                       "evidence_source":after.evidence_source})
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/evidence_dialogue_policy_v02318.json")
    args=p.parse_args()
    report={}
    for split,rows in [("development_seen",seen()),
                       ("prospective_v02318",[{"id":i,"text":t,"action":a} for i,t,a in NEW])]:
        result=evaluate(rows)
        old_correct=sum(r["old_correct"] for r in result)
        new_correct=sum(r["new_correct"] for r in result)
        question_ok=sum(r["question_format_ok"] for r in result)
        report[split]={"old_correct":old_correct,"new_correct":new_correct,
                       "question_format_ok":question_ok,"total":len(result),
                       "rows":result}
        print(f"{split}: old={old_correct}/{len(result)} new={new_correct}/{len(result)} question_format={question_ok}/{len(result)}")
        for r in result:
            if not r["new_correct"] or not r["question_format_ok"]:
                print(f' FAIL {r["id"]}: expected={r["expected"]} new={r["new_action"]} question={r["question"]}')
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",path)
if __name__=="__main__":main()
