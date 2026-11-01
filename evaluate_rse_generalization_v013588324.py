"""RSE v0.13.58.83.24: deterministic regression and generalization evaluation.

No model inference, no chat.py mutation; fresh temporary lifecycle store per case.
The examples are researcher-designed development probes, NOT independent holdout.
"""
import argparse,json,tempfile
from pathlib import Path
from rse_candidate_lifecycle_v013588322 import register,review
from rse_live_route_v013588323 import decide_live_route

Q="少しお話ししませんか？"
A="もちろん。何について話しましょう？"
SELECT="RSE_APPROVED_EXPERIMENTAL"
UNKNOWN="RSE_UNLEARNED_EXPERIMENTAL"
CASES=[
 {"id":"anchor-invite","query":Q,"expected":SELECT,"scenario":"approved"},
 {"id":"paraphrase-talk","query":"少し話しませんか？","expected":SELECT,"scenario":"approved"},
 {"id":"paraphrase-chat","query":"お話ししませんか？","expected":SELECT,"scenario":"approved"},
 {"id":"no-current-answer","query":"今何してる？","expected":UNKNOWN,"scenario":"approved"},
 {"id":"activity-paraphrase","query":"今何をしている？","expected":UNKNOWN,"scenario":"approved"},
 {"id":"unrelated-factual","query":"閃亜鉛鉱とは","expected":None,"scenario":"approved"},
 {"id":"unrelated-text","query":"今日は雨です","expected":None,"scenario":"approved"},
 {"id":"pending-not-selected","query":Q,"expected":UNKNOWN,"scenario":"pending"},
 {"id":"revoked-not-selected","query":Q,"expected":UNKNOWN,"scenario":"revoked"},
 {"id":"two-approved-collision","query":Q,"expected":"RSE_REVIEW_REQUIRED_EXPERIMENTAL","scenario":"collision"},
 {"id":"no-store","query":Q,"expected":UNKNOWN,"scenario":"empty"},
 {"id":"store-invalid","query":Q,"expected":"RSE_STORE_ERROR_EXPERIMENTAL","scenario":"invalid"}
]

def execute_case(case,root):
    store=root/(case["id"]+".json")
    scenario=case["scenario"]
    if scenario=="invalid":
        store.write_text("{broken",encoding="utf-8")
    if scenario not in {"empty","invalid"}:
        register(store,"invite",Q,A,"development-fixture")
        if scenario!="pending":
            review(store,"invite","APPROVED","synthetic-test")
        if scenario=="revoked":
            review(store,"invite","REVOKED","synthetic-test")
        if scenario=="collision":
            register(store,"invite_duplicate",Q,A,"development-fixture")
            review(store,"invite_duplicate","APPROVED","synthetic-test")
    answer=decide_live_route(case["query"],store)
    actual=answer["route"] if answer is not None else None
    return {"id":case["id"],"scenario":scenario,"query":case["query"],
            "expected":case["expected"],"actual":actual,"pass":actual==case["expected"],
            "answer":answer["answer"] if answer is not None else None}

def evaluate():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        cases=[execute_case(c,root) for c in CASES]
    total=len(cases);passed=sum(x["pass"] for x in cases)
    negative=[x for x in cases if x["expected"]!=SELECT]
    false_adoptions=sum(x["actual"]==SELECT for x in negative)
    positive=[x for x in cases if x["expected"]==SELECT]
    positive_hits=sum(x["actual"]==SELECT for x in positive)
    return {"status":"PASS" if passed==total else "FAIL",
            "scope":"DEVELOPMENT_FIXTURES_NOT_INDEPENDENT_HOLDOUT",
            "total":total,"passed":passed,
            "positive_coverage":positive_hits/len(positive) if positive else None,
            "negative_false_adoptions":false_adoptions,
            "negative_count":len(negative),
            "chat_py_executed":False,"model_inference":False,
            "cases":cases}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/rse_generalization_eval_v013588324.json")
    a=p.parse_args()
    result=evaluate()
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["status"]!="PASS":raise SystemExit(1)
if __name__=="__main__":main()
