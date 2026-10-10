"""v0.2.33.42 — unseen-phrase probe, matched policy comparison.

A developer-authored challenge set, not independent real-user data.
No model training or production memory integration.
"""
import argparse,json,tempfile
from pathlib import Path
from real_dss_reference_bridge_v023339 import RealDSSBridge
from clarification_interruption_v023340 import InterruptibleDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

# Each scenario has a reference input, then a follow-up whose desired route is
# annotated separately. These examples were NOT used in v0.2.33.41 fixtures.
PROBES=[
 ("fresh_goal_1","昨日の実験の続きをやって","Pythonの使い方を教えて","real_dss"),
 ("fresh_goal_2","前回の実験を再開して","画像認識を作りたい","real_dss"),
 ("fresh_goal_3","昨日の実験の続きをやって","LLMの不具合を修正したい","real_dss"),
 ("topic_change_1","昨日の実験の続きをやって","やっぱりAIを勉強したい","real_dss"),
 ("topic_change_2","前回の実験を再開して","代わりにPythonを開発したい","real_dss"),
 ("indirect_switch_1","昨日の実験の続きをやって","別件を先に相談したい","real_dss"),
 ("indirect_switch_2","前回の実験を再開して","今日は雑談にしよう","real_dss"),
 ("reply_jp_cursor","昨日の実験の続きをやって","カーソルの方","reference_resolution"),
 ("reply_jp_memory","前回の実験を再開して","意味記憶の実験","reference_resolution"),
 ("reply_ambiguous","昨日の実験の続きをやって","分からない","reference_resolution"),
 ("new_reference_1","前回の実験を再開して","この間の作業を再開して","reference_resolution"),
 ("new_reference_2","昨日の実験の続きをやって","この前の続きでお願い","reference_resolution"),
]
# Evaluate next-route AND state; a route-only hit can still be a failure
# (e.g. 'unknown' reply gets an inappropriate confirm).
EXPECTED_STATUS={
 "fresh_goal_1":"dss","fresh_goal_2":"dss","fresh_goal_3":"dss",
 "topic_change_1":"dss","topic_change_2":"dss",
 "indirect_switch_1":"dss","indirect_switch_2":"dss",
 "reply_jp_cursor":"confirm","reply_jp_memory":"confirm",
 "reply_ambiguous":"clarify",
 "new_reference_1":"clarify","new_reference_2":"clarify",
}
def compare():
    all_rows=[]
    for id,first,second,want_route in PROBES:
        arms={}
        for arm,klass in [("v023339",RealDSSBridge),("v023340",InterruptibleDSSBridge)]:
            with tempfile.TemporaryDirectory() as td:
                mem=JsonCandidateStore(Path(td)/"shadow.json")
                controller=klass(mem)
                init=controller.receive(first,"heldout-A")
                result=controller.receive(second,"heldout-A")
                actual_route=result.get("route")
                actual_status=result.get("status")
                predicted=mem._read()["records"]
                arms[arm]={"initial_status":init["status"],"route":actual_route,
                  "status":actual_status,"response":result.get("response",""),
                  "route_match":actual_route==want_route,
                  "status_match":actual_status==EXPECTED_STATUS[id],
                  "approved_without_confirmation":sum(x["status"]=="approved" for x in predicted)}
        all_rows.append({"id":id,"first":first,"second":second,"expected_route":want_route,
                         "expected_status":EXPECTED_STATUS[id],"arms":arms})
    summary={}
    for arm in ("v023339","v023340"):
        summary[arm]={"route_correct":sum(x["arms"][arm]["route_match"] for x in all_rows),
           "status_correct":sum(x["arms"][arm]["status_match"] for x in all_rows),
           "both_correct":sum(x["arms"][arm]["route_match"] and x["arms"][arm]["status_match"] for x in all_rows),
           "false_approvals":sum(x["arms"][arm]["approved_without_confirmation"] for x in all_rows)}
    return {"version":"v0.2.33.42","cases":len(PROBES),"summary":summary,
       "cases_detail":all_rows,
       "limitations":["Researcher-authored, independent of v0.2.33.41 fixtures but not independently collected",
           "Status labels represent desired behavior, not gold semantic understanding",
           "Neither arm has learned Japanese paraphrase generalization",
           "No production DSS memory writes or model updates"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/heldout_clarification_eval_v023342.json")
    a=p.parse_args()
    out=Path(a.out)
    if out.exists():raise FileExistsError("Refusing overwrite")
    result=compare()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    print("Saved",out)
if __name__=="__main__":main()
