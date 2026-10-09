"""Compare frozen v0.2.31.9 DSS against contextual composition controller."""
import argparse,json
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState,step as baseline
from contextual_purpose_composition_v02321 import step as composed
from multiturn_purpose_holdout_v02320 import fixture as seen

FRESH=[
 {"id":"ref-dev","turns":["LLMを勉強したい","それを自作したい"],
  "actions":["HANDOFF","HANDOFF"],"purpose":["development"],"topic":"LLM","relation":"UNSPECIFIED"},
 {"id":"plan-append","turns":["Pythonを学習したい","その後、開発もしたい"],
  "actions":["HANDOFF","PLAN"],"purpose":["learning","development"],"topic":"Python","relation":"SEQUENTIAL"},
 {"id":"plan-expand","turns":["画像認識を開発したい","さらに勉強もしたい"],
  "actions":["HANDOFF","PLAN"],"purpose":["development","learning"],"topic":"画像認識","relation":"UNSPECIFIED"},
 {"id":"explicit-switch","turns":["Pythonを勉強したい","やっぱりLLMを開発したい"],
  "actions":["HANDOFF","HANDOFF"],"purpose":["development"],"topic":"LLM","relation":"UNSPECIFIED"},
 {"id":"no-reference","turns":["Pythonを勉強したい","何について話しましょう"],
  "actions":["HANDOFF","ASK_CLARIFICATION"],"purpose":["learning"],"topic":"Python","relation":"UNSPECIFIED"},
 {"id":"confirm-reject","turns":["Pythonに興味がある","いいえ","Pythonを勉強したい"],
  "actions":["ASK_CONFIRMATION","ASK_CLARIFICATION","HANDOFF"],"purpose":["learning"],"topic":"Python","relation":"UNSPECIFIED"},
]
def evaluate(scenarios,fn):
    result=[]
    for case in scenarios:
        state=DialogueState();actions=[]
        for utterance in case["turns"]:
            state,action,_=fn(state,utterance);actions.append(action)
        checks={"actions":actions==case["actions"],
                "purposes":state.purposes==case["purpose"],
                "topic":state.topic==case["topic"],
                "relation":state.relation==case.get("relation",state.relation),
                "history":len(state.history)==len(case["turns"])}
        result.append({"id":case["id"],"checks":checks,
                       "all_correct":all(checks.values()),"actions":actions,
                       "purposes":state.purposes,"topic":state.topic,"relation":state.relation})
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/contextual_purpose_composition_v02321.json")
    args=p.parse_args()
    report={}
    for split,scenarios in (("development_seen",seen()),("prospective_v02321",FRESH)):
        for name,fn in (("baseline",baseline),("composed",composed)):
            rows=evaluate(scenarios,fn)
            correct=sum(r["all_correct"] for r in rows)
            report[split+"/"+name]={"correct":correct,"total":len(rows),"rows":rows}
            print(f"{split}/{name}: {correct}/{len(rows)}")
            for r in rows:
                if not r["all_correct"]:
                    print(f' FAIL {r["id"]}: {",".join(k for k,v in r["checks"].items() if not v)}')
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",out)
if __name__=="__main__":main()
