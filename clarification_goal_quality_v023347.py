"""v0.2.33.47 — goal quality, question relevance and interaction cost.

Matched diagnostic scenarios; no modification of existing policies.
Developer-authored cases are not independent human-labeled benchmarks.
"""
import argparse,json,tempfile
from pathlib import Path
from clarification_interruption_v023340 import InterruptibleDSSBridge
from context_aware_clarification_v023345 import ContextAwareBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

ARMS={"v023340":InterruptibleDSSBridge,"v023345":ContextAwareBridge}
SCENARIOS=[
 {"id":"canonical","steps":[("input","昨日の実験の続きをやって"),("input","cursor"),("confirm",True)],
  "goal":"cursor","relevance":["experiment","experiment",None]},
 {"id":"polite_cursor","steps":[("input","昨日の実験の続きをやって"),("input","カーソルでお願いします"),("confirm",True)],
  "goal":"cursor","relevance":["experiment","experiment",None]},
 {"id":"polite_semantic","steps":[("input","前回の実験を再開して"),("input","意味記憶のほうです"),("confirm",True)],
  "goal":"semantic_memory","relevance":["experiment","experiment",None]},
 {"id":"reject_and_recover","steps":[("input","前回の実験を再開して"),("input","cursor"),("confirm",False),
       ("input","前回の実験を再開して"),("input","semantic_memory"),("confirm",True)],
  "goal":"semantic_memory","relevance":["experiment","experiment",None,"experiment","experiment",None]},
 {"id":"indirect_switch","steps":[("input","昨日の実験の続きをやって"),("input","その前に違う件を聞きたい")],
  "goal":"switch","relevance":["experiment","new_goal"]},
 {"id":"explicit_switch","steps":[("input","昨日の実験の続きをやって"),("input","LLMを勉強したい")],
  "goal":"switch","relevance":["experiment",None]},
 {"id":"cancel","steps":[("input","昨日の実験の続きをやって"),("input","キャンセル")],
  "goal":"cancel","relevance":["experiment",None]},
]
def question_kind(reply):
    if reply.get("status")=="confirm":return "experiment"
    if reply.get("status")=="clarify" and reply.get("route")=="reference_resolution":return "experiment"
    if reply.get("status")=="dss" and reply.get("action") in ("ASK_CLARIFICATION","ASK_CONFIRMATION"):
        return "new_goal"
    return None
def run():
    details=[]
    for spec in SCENARIOS:
        outcomes={}
        for name,cls in ARMS.items():
            with tempfile.TemporaryDirectory() as td:
                memory=JsonCandidateStore(Path(td)/"shadow.json")
                bridge=cls(memory);trace=[];prompt_count=0;relevant=0;irrelevant=0;found=None
                for index,(operation,value) in enumerate(spec["steps"],1):
                    result=bridge.confirm(value,"A") if operation=="confirm" else bridge.receive(value,"A")
                    kind=question_kind(result)
                    desired=spec["relevance"][index-1]
                    if kind:
                        prompt_count+=1
                        if kind==desired:relevant+=1
                        else:irrelevant+=1
                    if found is None and (result["status"]=="resolved" or
                        (spec["goal"]=="switch" and result.get("route")=="real_dss") or
                        (spec["goal"]=="cancel" and result["status"]=="cancelled")):
                        found=index
                    trace.append({"turn":index,"status":result["status"],"route":result.get("route"),
                                  "question_kind":kind,"expected_question_kind":desired,
                                  "value":result.get("value")})
                saved=memory.lookup("A","experiment","target")
                goal_ok=(saved==spec["goal"] if spec["goal"] not in ("switch","cancel")
                         else any((spec["goal"]=="switch" and r["route"]=="real_dss") or
                                  (spec["goal"]=="cancel" and r["status"]=="cancelled") for r in trace))
                if spec["goal"] in ("switch","cancel"):goal_ok=goal_ok and saved is None
                outcomes[name]={"goal_resolved_correctly":goal_ok,"questions":prompt_count,
                     "relevant_questions":relevant,"irrelevant_questions":irrelevant,
                     "turns_to_goal":found if goal_ok else None,
                     "user_input_turns":sum(x[0]=="input" for x in spec["steps"]),
                     "approved_value":saved,"trace":trace}
        details.append({"id":spec["id"],"goal":spec["goal"],"arms":outcomes})
    summary={}
    for arm in ARMS:
        rows=[x["arms"][arm] for x in details]
        turns=[x["turns_to_goal"] for x in rows if x["goal_resolved_correctly"] and x["turns_to_goal"]]
        summary[arm]={"goals_correct":sum(x["goal_resolved_correctly"] for x in rows),
            "total_goals":len(rows),"questions":sum(x["questions"] for x in rows),
            "relevant_questions":sum(x["relevant_questions"] for x in rows),
            "irrelevant_questions":sum(x["irrelevant_questions"] for x in rows),
            "mean_turns_conditional_on_success":sum(turns)/len(turns) if turns else None,
            "penalized_turn_cost":sum(x["turns_to_goal"] if x["goal_resolved_correctly"] and x["turns_to_goal"]
               else len(details[i]["arms"][arm]["trace"])+3 for i,x in enumerate(rows))/len(rows)}
    return {"version":"v0.2.33.47","summary":summary,"details":details,
      "limitations":["Researcher-designed cases and question-kind labels, not independent users",
       "Question relevance is a narrow slot-type proxy, not textual helpfulness",
       "Turn cost penalizes unresolved trajectories by observed turns plus three",
       "Explicit confirm() is a test harness action, not a natural-language yes parser",
       "Purpose DSS project code; reference memory is experimental JSON shadow only"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/clarification_goal_quality_v023347.json")
    args=p.parse_args();path=Path(args.out)
    if path.exists():raise FileExistsError("Refusing to overwrite")
    result=run();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
