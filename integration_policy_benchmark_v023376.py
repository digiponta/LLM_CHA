"""LLM_CHA v0.2.33.76: repeatable deterministic integration policy benchmark.

Invokes the same routing, quality and truth-gate functions imported by chat.py.
This is *not* a GPU/chat.py end-to-end test and cannot measure model quality.
"""
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
from multi_intent_reference_v023375 import split_input,clarify_reference
from generated_response_quality_v023374 import greeting_repair
from truth_aware_corpus_gate_v023373 import corpus_answer_decision

CASES=(
    ("M01","routing","こんにちは、宇宙について教えて","宇宙とは","GREETING_PLUS_KNOWLEDGE"),
    ("M02","routing","こんばんは、量子力学とは","量子力学とは","GREETING_PLUS_KNOWLEDGE"),
    ("M03","routing","こんにちは、宇宙について教えて、それと時間も","こんにちは、宇宙について教えて、それと時間も",None),
    ("M04","routing","/truth 宇宙","/truth 宇宙",None),
    ("M05","routing","宇宙とは","宇宙とは",None),
    ("R01","reference","昨日の続き","昨日の続き","REFERENCE_CLARIFY"),
    ("R02","reference","あの実験","あの実験","REFERENCE_CLARIFY"),
    ("R03","reference","昨日の続きで宇宙について教えて","昨日の続きで宇宙について教えて",None),
)
GREETINGS=(
    ("G01","こんにちは","こんにちは。元気障で 強く資源、 の後の前に注釈を呈する。",True,"こんにちは。"),
    ("G02","こんばんは","未学習です",False,"こんばんは。"),
    ("G03","こんにちは","こんにちは。",True,None),
    ("G04","こんにちは、宇宙について教えて","未学習です",False,None),
)
TRUTH=(
    ("T01","UNVERIFIED",True,"BLOCK_UNVERIFIED_CORPUS"),
    ("T02","CONTESTED",True,"BLOCK_UNVERIFIED_CORPUS"),
    ("T03","TRUE",True,"ALLOW_VERIFIED_STATE"),
    ("T04","FALSE",True,"DEFER_TRUTH_CORRECTION"),
    ("T05","OUTDATED",True,"DEFER_TRUTH_CORRECTION"),
    ("T06","TRUE",False,"MISS"),
)

def run_benchmark():
    rows=[]
    for cid,group,value,expected_text,expected_route in CASES:
        actual_text,actual_route=split_input(value)
        # Assert the actual reference clarification text is available, too.
        ok=(actual_text,actual_route)==(expected_text,expected_route)
        if actual_route=="REFERENCE_CLARIFY":
            ok=ok and "どの実験" in clarify_reference()
        rows.append({"id":cid,"group":group,"passed":bool(ok),
                     "expected":[expected_text,expected_route],
                     "observed":[actual_text,actual_route]})
    for cid,user,candidate,accepted,expected in GREETINGS:
        observed,reason=greeting_repair(user,candidate,accepted)
        rows.append({"id":cid,"group":"quality","passed":observed==expected,
                     "expected":expected,"observed":observed,"reason":reason})
    for cid,state,hit,expected in TRUTH:
        observed=corpus_answer_decision(state,hit)
        rows.append({"id":cid,"group":"truth","passed":observed==expected,
                     "expected":expected,"observed":observed})
    summary={}
    for group in sorted(set(r["group"] for r in rows)):
        selected=[r for r in rows if r["group"]==group]
        summary[group]={"passed":sum(r["passed"] for r in selected),"total":len(selected)}
    return {"version":"v0.2.33.76","kind":"deterministic-policy-integration",
            "limitations":"No chat.py invocation, GPU model generation, or evidence retrieval.",
            "passed":sum(r["passed"] for r in rows),
            "total":len(rows),"summary":summary,"cases":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/integration_policy_v023376.json")
    args=p.parse_args()
    report=run_benchmark()
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"total":report["total"],
                      "summary":report["summary"],"file":str(path)},ensure_ascii=False,indent=2))
    return 0 if report["passed"]==report["total"] else 1

if __name__=="__main__":sys.exit(main())
