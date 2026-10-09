"""v0.2.31.7 dialogue-policy comparison: known development and new prospective.

v0.2.31.6 22 rows are already inspected and now development diagnostics.
"""
import argparse,json
from pathlib import Path
from structured_purpose_holdout_v02316 import fixture as dev
from structured_semantic_purpose_v02315 import extract,action_for as old_action
from semantic_dialogue_policy_v02317 import decide

FRESH=[
 ("single-dev","Pythonでアプリを開発したい","HANDOFF"),
 ("single-error","LLMのエラーを直したい","HANDOFF"),
 ("casual","Pythonについて雑談したい","RESPOND"),
 ("casual-other","LLMのことをおしゃべりしたい","RESPOND"),
 ("multi-plain","LLMを勉強して開発もしたい","PLAN"),
 ("multi-seq","LLMを勉強してから開発したい","PLAN"),
 ("multi-alt","画像認識を学習し、開発もしたい","PLAN"),
 ("ambiguous","Pythonに興味がある","ASK_CONFIRMATION"),
 ("unknown","12345678","ASK_CLARIFICATION"),
 ("negation","Pythonは開発じゃなく勉強したい","HANDOFF"),
 ("multiple-cross","Pythonのエラーを直して開発したい","PLAN"),
 ("clear-learn","LLMを勉強したい","HANDOFF"),
]
def evaluate(rows):
    output=[]
    for r in rows:
        s=extract(r["text"])
        a=old_action(s)
        b=decide(s).action
        output.append({"id":r["id"],"text":r["text"],"expected":r["expected"],
                       "old":a,"new":b,"old_correct":a==r["expected"],
                       "new_correct":b==r["expected"],
                       "parser":{"purposes":s.purposes,"relation":s.relation,"status":s.status}})
    return output
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="results/semantic_dialogue_policy_v02317.json")
    a=ap.parse_args()
    sets={"development_seen":[{"id":r["id"],"text":r["text"],"expected":r["action"]} for r in dev()],
          "prospective_v02317":[{"id":id,"text":t,"expected":expected} for id,t,expected in FRESH]}
    report={}
    for split,rows in sets.items():
        result=evaluate(rows)
        old=sum(r["old_correct"] for r in result)
        new=sum(r["new_correct"] for r in result)
        print(f"{split}: old={old}/{len(result)} new={new}/{len(result)}")
        for r in result:
            if not r["new_correct"]:
                print(f' FAIL {r["id"]}: expected={r["expected"]} got={r["new"]} parser={r["parser"]}')
        report[split]={"old_correct":old,"new_correct":new,"total":len(result),"rows":result}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",out)
if __name__=="__main__":main()
