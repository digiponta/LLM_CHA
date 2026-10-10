"""LLM_CHA v0.2.33.46: matched multi-turn clarification efficiency evaluation.

Uses existing policy unchanged. Developer-authored diagnostic trajectories, NOT
independent real-user data or a claim of natural language generalization.
"""
import argparse,json,tempfile
from pathlib import Path
from clarification_interruption_v023340 import InterruptibleDSSBridge
from context_aware_clarification_v023345 import ContextAwareBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

SCENARIOS=[
 {"id":"canonical_success","steps":[("input","昨日の実験の続きをやって"),("input","cursor"),("confirm",True),("input","前回の実験を再開して")],
  "expected":["clarify","confirm","resolved","resolved"],"target":"cursor"},
 {"id":"polite_success","steps":[("input","昨日の実験の続きをやって"),("input","カーソルでお願いします"),("confirm",True),("input","前回の実験を再開して")],
  "expected":["clarify","confirm","resolved","resolved"],"target":"cursor"},
 {"id":"memory_success","steps":[("input","前回の実験を再開して"),("input","意味記憶のほうです"),("confirm",True)],
  "expected":["clarify","confirm","resolved"],"target":"semantic_memory"},
 {"id":"explicit_switch","steps":[("input","昨日の実験の続きをやって"),("input","AIを開発したい")],
  "expected":["clarify","dss"],"target":None},
 {"id":"indirect_switch","steps":[("input","昨日の実験の続きをやって"),("input","その前に違う件を聞きたい")],
  "expected":["clarify","dss"],"target":None},
 {"id":"reject_then_retry","steps":[("input","昨日の実験の続きをやって"),("input","cursor"),("confirm",False),("input","昨日の実験の続きをやって"),("input","semantic_memory"),("confirm",True)],
  "expected":["clarify","confirm","rejected","clarify","confirm","resolved"],"target":"semantic_memory"},
 {"id":"ambiguous_then_answer","steps":[("input","昨日の実験の続きをやって"),("input","カーソルと意味記憶の両方"),("input","cursor"),("confirm",True)],
  "expected":["clarify","clarify","confirm","resolved"],"target":"cursor"},
 {"id":"cancel","steps":[("input","昨日の実験の続きをやって"),("input","キャンセル")],
  "expected":["clarify","cancelled"],"target":None},
 {"id":"switch_after_candidate","steps":[("input","前回の実験を再開して"),("input","cursor"),("input","それよりLLMを勉強したい")],
  "expected":["clarify","confirm","dss"],"target":None},
 {"id":"other_context","steps":[("input","昨日の実験の続きをやって"),("input","cursor"),("confirm",True),("input","前回の実験を再開して","B")],
  "expected":["clarify","confirm","resolved","clarify"],"target":"cursor"}
]
ARMS={"v023340":InterruptibleDSSBridge,"v023345":ContextAwareBridge}
def evaluate():
    results=[]
    for scenario in SCENARIOS:
        arms={}
        for name,klass in ARMS.items():
            with tempfile.TemporaryDirectory() as td:
                memory=JsonCandidateStore(Path(td)/"candidates.json")
                bridge=klass(memory)
                observed=[];questions=0;completed_at=None
                for index,step in enumerate(scenario["steps"]):
                    operation,value=step[:2]
                    context=step[2] if len(step)>2 else "A"
                    answer=bridge.confirm(value,context) if operation=="confirm" else bridge.receive(value,context)
                    status=answer["status"]
                    if status=="clarify" or (status=="dss" and answer.get("action") in ("ASK_CLARIFICATION","ASK_CONFIRMATION")) or status=="confirm":
                        questions+=1
                    if status=="resolved" and completed_at is None:completed_at=index+1
                    observed.append({"status":status,"route":answer.get("route"),"context":context,
                                     "response":answer.get("response"),"value":answer.get("value")})
                correct=sum(x["status"]==y for x,y in zip(observed,scenario["expected"]))
                approved=memory._read()["records"]
                final=memory.lookup("A","experiment","target")
                arms[name]={"step_correct":correct,"step_total":len(observed),
                   "all_steps_correct":correct==len(observed),
                   "question_events":questions,
                   "turns_to_first_resolution":completed_at,
                   "approved_value":final,
                   "unexpected_approval":int(final is not None and final!=scenario["target"]),
                   "approved_count":sum(r["status"]=="approved" for r in approved),
                   "trace":observed}
        results.append({"id":scenario["id"],"expected_status":scenario["expected"],"arms":arms})
    summary={}
    for name in ARMS:
        v=[r["arms"][name] for r in results]
        resolved=[x["turns_to_first_resolution"] for x in v if x["turns_to_first_resolution"] is not None]
        summary[name]={"exact_trajectories":sum(x["all_steps_correct"] for x in v),
          "trajectories":len(v),"step_accuracy":sum(x["step_correct"] for x in v)/sum(x["step_total"] for x in v),
          "question_events":sum(x["question_events"] for x in v),
          "resolved_trajectories":len(resolved),
          "mean_turns_to_first_resolution":sum(resolved)/len(resolved) if resolved else None,
          "unexpected_approvals":sum(x["unexpected_approval"] for x in v)}
    return {"version":"v0.2.33.46","summary":summary,"scenarios":results,
       "limitations":["Hand-authored diagnostic trajectories, not independently collected",
           "Question events include confirmations and DSS requests, not just referent prompts",
           "Context B isolation checked as step status; no model generation evaluated",
           "Approval requires explicit confirm(True), and all storage is shadow-only"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/multiturn_clarification_efficiency_v023346.json")
    args=p.parse_args();target=Path(args.out)
    if target.exists():raise FileExistsError("Refusing to overwrite")
    result=evaluate();target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    print("Saved",target)
if __name__=="__main__":main()
