"""v0.2.33.48: honest end-to-end dialogue handoff evaluation.

Evaluates existing ContextAwareBridge unchanged. Natural yes/no handling is
a TEST ADAPTER (not yet a production feature), and outcomes are separated:
reference approved, DSS goal identified, handoff only, cancelled, unresolved.
"""
import argparse,json,re,tempfile
from pathlib import Path
from context_aware_clarification_v023345 import ContextAwareBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

YES={"はい","はい、お願いします","それで合っています","そうです"}
NO={"いいえ","違います","違います、やめます"}
def normalized(text):return str(text).strip().replace("。","").replace("！","")
def receive_harness(bridge,text,context="A"):
    """Test adapter; does NOT change deployed receive() behavior."""
    resolver=bridge._resolver(context)
    value=normalized(text)
    if resolver.pending and resolver.pending.get("candidate") and value in YES:
        return bridge.confirm(True,context)
    if resolver.pending and resolver.pending.get("candidate") and value in NO:
        return bridge.confirm(False,context)
    return bridge.receive(text,context)
# Deliberately explicit labels rather than calling any DSS route a completed goal.
SCENARIOS=[
 {"id":"yes_cursor","turns":["昨日の実験の続きをやって","カーソルでお願いします","はい"],
  "expected":"reference_approved","target":"cursor"},
 {"id":"no_retry","turns":["昨日の実験の続きをやって","cursor","いいえ","昨日の実験の続きをやって","semantic_memory","はい"],
  "expected":"reference_approved","target":"semantic_memory"},
 {"id":"handoff_goal_clarified","turns":["昨日の実験の続きをやって","その前に違う件を聞きたい","LLMを勉強したい"],
  "expected":"dss_goal_identified","target":None},
 {"id":"handoff_still_unresolved","turns":["昨日の実験の続きをやって","その前に違う件を聞きたい"],
  "expected":"handoff_only","target":None},
 {"id":"cancel","turns":["前回の実験を再開して","キャンセル"],
  "expected":"cancelled","target":None},
 {"id":"unresolved","turns":["昨日の実験の続きをやって","分からない","まだ分からない"],
  "expected":"unresolved","target":None},
 {"id":"context_isolation","turns":["昨日の実験の続きをやって","カーソルの方","はい"],
  "expected":"reference_approved","target":"cursor","isolation":True},
]
def evaluate():
    details=[]
    for scenario in SCENARIOS:
        with tempfile.TemporaryDirectory() as td:
            store=JsonCandidateStore(Path(td)/"shadow.json")
            bridge=ContextAwareBridge(store)
            trace=[];questions=0
            for text in scenario["turns"]:
                r=receive_harness(bridge,text)
                questions+=int(r["status"] in ("clarify","confirm") or
                    (r["status"]=="dss" and r.get("action") in ("ASK_CLARIFICATION","ASK_CONFIRMATION")))
                trace.append({"input":text,"status":r["status"],"route":r.get("route"),
                              "action":r.get("action"),"purpose":r.get("purpose"),
                              "value":r.get("value"),"response":r.get("response")})
            approved=store.lookup("A","experiment","target")
            statuses=[x["status"] for x in trace]
            if approved is not None:outcome="reference_approved"
            elif statuses[-1]=="cancelled":outcome="cancelled"
            elif any(x["route"]=="real_dss" and x["purpose"] is not None for x in trace):
                outcome="dss_goal_identified"
            elif any(x["route"]=="real_dss" for x in trace):outcome="handoff_only"
            else:outcome="unresolved"
            isolated=True
            if scenario.get("isolation"):
                b=receive_harness(bridge,"前回の実験を再開して","B")
                isolated=b["status"]=="clarify"
            correct=(outcome==scenario["expected"] and
                (scenario["target"] is None or approved==scenario["target"]) and isolated)
            details.append({"id":scenario["id"],"expected":scenario["expected"],
                            "observed":outcome,"correct":correct,
                            "user_turns":len(scenario["turns"]),"question_events":questions,
                            "approved":approved,"context_isolated":isolated,"trace":trace})
    return {"version":"v0.2.33.48","cases":len(details),
       "correct":sum(x["correct"] for x in details),
       "reference_approved":sum(x["observed"]=="reference_approved" for x in details),
       "dss_goal_identified":sum(x["observed"]=="dss_goal_identified" for x in details),
       "handoff_only":sum(x["observed"]=="handoff_only" for x in details),
       "cancelled":sum(x["observed"]=="cancelled" for x in details),
       "unresolved":sum(x["observed"]=="unresolved" for x in details),
       "question_events":sum(x["question_events"] for x in details),
       "details":details,
       "limitations":["Developer-authored development fixtures, not unseen user samples",
          "Yes/no parsing is a test harness adapter, NOT integrated runtime",
          "DSS goal identification is not successful execution of the goal",
          "Question-events count prompts and may miss content-based implicit questions",
          "Shadow memory only; no production Semantic Memory or LLM update"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/e2e_dialogue_resolution_v023348.json")
    a=p.parse_args();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    r=evaluate();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({k:r[k] for k in ("cases","correct","reference_approved","dss_goal_identified","handoff_only","cancelled","unresolved","question_events")},ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
