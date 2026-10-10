"""v0.2.33.44 independent-style clarification robustness audit.

New challenge cases are separated into development and locked final sets.
No parameter fitting or rule changes occur; "final" remains developer-authored
and is not independently collected user data.
"""
import argparse,json,tempfile
from pathlib import Path
from clarification_normalization_v023343 import NormalizedClarificationBridge
from clarification_interruption_v023340 import InterruptibleDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

# Distinct text from earlier v0.2.33.42 probes; not representative sampling.
DEV=[
 ("negated_answer","昨日の実験の続きをやって","カーソルではなく意味記憶","clarify",None),
 ("two_answers","前回の実験を再開して","カーソルと意味記憶の両方","clarify",None),
 ("polite_answer","昨日の実験の続きをやって","カーソルでお願いします","confirm","cursor"),
 ("indirect_goal","前回の実験を再開して","一旦ほかの話をしましょう","dss",None),
 ("explicit_goal","昨日の実験の続きをやって","AIについて教えて","dss",None),
 ("uncertainty","前回の実験を再開して","まだ決めかねています","clarify",None),
]
FINAL=[
 ("negated_reverse","昨日の実験の続きをやって","意味記憶ではなくカーソル","clarify",None),
 ("contradiction","前回の実験を再開して","カーソル、いや意味記憶","clarify",None),
 ("ambiguous_choice","昨日の実験の続きをやって","どっちでもいい","clarify",None),
 ("topic_detour","前回の実験を再開して","その前に違う件を聞きたい","dss",None),
 ("polite_memory","昨日の実験の続きをやって","意味記憶のほうです","confirm","semantic_memory"),
 ("canonical_cursor","前回の実験を再開して","cursor","confirm","cursor"),
 ("new_learning_goal","昨日の実験の続きをやって","画像認識を勉強したい","dss",None),
 ("indirect_resume","前回の実験を再開して","前にやった作業をもう一度","clarify",None),
]
ARMS={"v023340":InterruptibleDSSBridge,"v023343":NormalizedClarificationBridge}
def evaluate_cases(rows):
    details=[]
    for id,first,follow,want_status,want_value in rows:
        arm_data={}
        for name,cls in ARMS.items():
            with tempfile.TemporaryDirectory() as td:
                store=JsonCandidateStore(Path(td)/"shadow.json")
                b=cls(store)
                start=b.receive(first,"eval")
                response=b.receive(follow,"eval")
                candidates=store._read()["records"]
                actual_value=response.get("value")
                matched=response["status"]==want_status and (want_value is None or actual_value==want_value)
                arm_data[name]={"initial_status":start["status"],
                    "status":response["status"],"route":response.get("route"),
                    "value":actual_value,"match":matched,
                    "approved_without_confirmation":sum(x["status"]=="approved" for x in candidates),
                    "candidate_count":len(candidates)}
        details.append({"id":id,"first":first,"followup":follow,
            "expected_status":want_status,"expected_value":want_value,"arms":arm_data})
    return details
def summarize(details):
    return {arm:{"correct":sum(r["arms"][arm]["match"] for r in details),
                 "total":len(details),
                 "unapproved_promotions":sum(r["arms"][arm]["approved_without_confirmation"] for r in details)}
            for arm in ARMS}
def run():
    dev=evaluate_cases(DEV)
    final=evaluate_cases(FINAL)
    return {"version":"v0.2.33.44","development":{"summary":summarize(dev),"cases":dev},
            "final":{"summary":summarize(final),"cases":final},
            "constraints":["No adjustment to either policy based on final cases",
                           "Developer-authored challenge set, not truly external independent annotation",
                           "Only status and selected candidate checked; no natural language understanding benchmark",
                           "No live Semantic Memory, LLM training or production mutations"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/clarification_robustness_v023344.json")
    a=p.parse_args();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    result=run();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"development":result["development"]["summary"],
                      "final":result["final"]["summary"]},ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
