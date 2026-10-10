"""LLM_CHA v0.2.33.41 — held-out scenario clarification policy evaluation.

Deterministic, hand-curated evaluation; NOT a statistical estimate of general
Japanese intent classification. Per-scenario isolated temporary shadow memory.
"""
import argparse,json,tempfile
from pathlib import Path
from clarification_interruption_v023340 import InterruptibleDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

CASES=[
 {"id":"known_learning","turns":[["LLMを勉強したい","real_dss"]],"label":"known"},
 {"id":"known_development","turns":[["Pythonを開発したい","real_dss"]],"label":"known"},
 {"id":"known_troubleshooting","turns":[["LLMのエラーを修正したい","real_dss"]],"label":"known"},
 {"id":"known_casual","turns":[["雑談したい","real_dss"]],"label":"known"},
 {"id":"clarify_yesterday","turns":[["昨日の実験の続きをやって","reference_resolution"]],"label":"clarify"},
 {"id":"clarify_previous","turns":[["前回の実験を再開して","reference_resolution"]],"label":"clarify"},
 {"id":"answer_cursor","turns":[["昨日の実験の続きをやって","reference_resolution"],["cursor","reference_resolution"]],"label":"clarification_answer"},
 {"id":"answer_sem","turns":[["前回の実験を再開して","reference_resolution"],["semantic_memory","reference_resolution"]],"label":"clarification_answer"},
 {"id":"interrupt_goal","turns":[["昨日の実験の続きをやって","reference_resolution"],["AIを開発したい","real_dss"]],"label":"switch"},
 {"id":"interrupt_other_goal","turns":[["前回の実験を再開して","reference_resolution"],["LLMを学習したい","real_dss"]],"label":"switch"},
 {"id":"interrupt_after_candidate","turns":[["昨日の実験の続きをやって","reference_resolution"],["cursor","reference_resolution"],["それよりLLMを勉強したい","real_dss"]],"label":"switch_after_candidate"},
 {"id":"cancel","turns":[["昨日の実験の続きをやって","reference_resolution"],["キャンセル","reference_resolution"]],"label":"cancel"},
 {"id":"non_answer","turns":[["昨日の実験の続きをやって","reference_resolution"],["よく分からない","reference_resolution"]],"label":"clarification_answer"},
 {"id":"unknown_copy","turns":[["XYZ 未知トークン列","real_dss"]],"label":"known"},
]
def evaluate(cases=CASES):
    rows=[];route_hits=0;route_total=0;unnecessary=0;ordinary=0
    required=0;required_hit=0;switch=0;switch_hit=0;false_approval=0;leaks=0
    for case in cases:
        with tempfile.TemporaryDirectory() as td:
            store=JsonCandidateStore(Path(td)/"shadow.json")
            bridge=InterruptibleDSSBridge(store)
            obs=[]
            for utterance,expected in case["turns"]:
                got=bridge.receive(utterance,"eval-A")
                obs.append({"input":utterance,"expected_route":expected,
                            "actual_route":got["route"],"status":got["status"],
                            "match":got["route"]==expected})
                route_total+=1;route_hits+=int(got["route"]==expected)
            label=case["label"]
            if label=="known":
                ordinary+=1;unnecessary+=int(obs[0]["actual_route"]=="reference_resolution")
            if label=="clarify":
                required+=1;required_hit+=int(obs[0]["status"]=="clarify")
            if label.startswith("switch"):
                switch+=1;switch_hit+=int(obs[-1]["actual_route"]=="real_dss")
            false_approval+=sum(x["status"]=="approved" for x in store._read()["records"])
            leaks+=int(store.lookup("eval-B","experiment","target") is not None)
            rows.append({"id":case["id"],"label":label,"steps":obs,
                         "all_routes_match":all(x["match"] for x in obs),
                         "approved_records":sum(x["status"]=="approved" for x in store._read()["records"])})
    return {"cases":len(cases),"turns":route_total,"correct_routes":route_hits,
       "route_accuracy":route_hits/route_total if route_total else None,
       "unnecessary_question_rate":unnecessary/ordinary if ordinary else None,
       "needed_question_recall":required_hit/required if required else None,
       "switch_success_rate":switch_hit/switch if switch else None,
       "false_approval_count":false_approval,"cross_context_leaks":leaks,
       "case_results":rows,
       "limitations":["Hand-authored narrow policy fixtures; not independent real-user distribution",
       "False approval measures accidental approved records only (no confirm calls)",
       "Cross-context leakage is checked against per-case shadow store",
       "No live Semantic Memory or natural-language generation involved"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/clarification_policy_eval_v023341.json")
    a=p.parse_args()
    result=evaluate();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("case_results","limitations")},indent=2))
    print("Saved",path)
if __name__=="__main__":main()
