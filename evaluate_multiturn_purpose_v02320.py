"""Frozen multi-turn DSS diagnostic; records all failures, no tuning."""
import argparse,json
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState,step
from multiturn_purpose_holdout_v02320 import fixture
def evaluate(cases):
    results=[]
    for case in cases:
        d=DialogueState();actions=[];replies=[]
        for utterance in case["turns"]:
            d,action,reply=step(d,utterance)
            actions.append(action);replies.append(reply)
        checks={
            "actions":actions==case["actions"],
            "purposes":d.purposes==case["purpose"],
            "topic":d.topic==case["topic"],
            "relation":d.relation==case.get("relation",d.relation),
            "history":len(d.history)==len(case["turns"]),
            "question_consistency":all(
                bool(h["response"]) and h["action"]==actions[i]
                for i,h in enumerate(d.history)),
        }
        results.append({"id":case["id"],"turns":case["turns"],
                        "expected_actions":case["actions"],"actual_actions":actions,
                        "expected_purposes":case["purpose"],"actual_purposes":d.purposes,
                        "expected_topic":case["topic"],"actual_topic":d.topic,
                        "expected_relation":case.get("relation"),
                        "actual_relation":d.relation,"responses":replies,
                        "checks":checks,"all_correct":all(checks.values())})
    return results
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/multiturn_purpose_v02320.json")
    args=p.parse_args()
    rows=evaluate(fixture())
    keys=next(iter(rows))["checks"]
    for row in rows:
        fail=[k for k,v in row["checks"].items() if not v]
        print(f'{row["id"]}: {"PASS" if not fail else "FAIL"}'
              f' {",".join(fail)} actions={row["actual_actions"]}'
              f' purpose={row["actual_purposes"]} topic={row["actual_topic"]}')
    for k in keys:
        print(f'{k}: {sum(r["checks"][k] for r in rows)}/{len(rows)}')
    print(f'Full scenarios: {sum(r["all_correct"] for r in rows)}/{len(rows)}')
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",target)
if __name__=="__main__":main()
