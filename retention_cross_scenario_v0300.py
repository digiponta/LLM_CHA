"""LLM_CHA v0.3.0 cross-scenario adaptive retention sweep.

Independent deterministic scenario traces; no writes to conversation data,
Truth State, Semantic Memory or model weights.
"""
from __future__ import annotations
import json
from pathlib import Path
from adaptive_retention_eval_v023351 import Event, POLICIES, simulate

def scenarios():
    # Separately authored traces, not train/validation splits.
    return {
        "short_switch": [Event("observe","宇宙"),Event("observe","数学"),Event("observe","GPU"),
                         Event("query","宇宙"),Event("query","数学"),Event("query","GPU")],
        "delayed_return": [Event("observe","宇宙",True)] +
            [Event("observe",f"一時{i}") for i in range(12)] +
            [Event("query","宇宙",True),Event("query","一時11")],
        "frequency_skew": [Event("observe","宇宙")]*8 +
            [Event("observe","GPU"),Event("observe","一時0"),
             Event("observe","一時1"),Event("query","宇宙"),
             Event("query","一時1")],
        "pin_saturation": [Event("observe",f"重要{i}",True) for i in range(4)] +
            [Event("observe",f"新規{i}",True) for i in range(8)] +
            [Event("query",f"重要{i}",True) for i in range(4)] +
            [Event("query",f"新規{i}",True) for i in range(8)],
        "topic_churn": [Event("observe",f"話題{i}") for i in range(16)] +
            [Event("query",f"話題{i}") for i in range(16)],
    }

def sweep(capacities=(2,4,8)):
    rows=[]
    for name,events in scenarios().items():
        for capacity in capacities:
            if not isinstance(capacity,int) or capacity<1 or capacity>16:
                raise ValueError("invalid capacity")
            for policy in POLICIES:
                metrics=simulate(events,policy,capacity)
                rows.append({"scenario":name,"events":len(events),**metrics})
    return {"version":"v0.3.0","independent_scenarios":len(scenarios()),
            "capacities":list(capacities),"rows":rows,
            "caution":"synthetic fixtures; not real conversational quality or truth validation"}

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",default="results/retention_cross_scenario_v0300.json")
    args=parser.parse_args()
    report=sweep()
    path=Path(args.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"v0.3.0 scenarios={report['independent_scenarios']} capacity_values={report['capacities']} rows={len(report['rows'])}")
    for row in report["rows"]:
        print(f"{row['scenario']:16s} cap={row['capacity']:2d} {row['policy']:12s} "
              f"success={row['return_success_rate']} important={row['important_retention_rate']} "
              f"refusals={row['protected_insertion_refusals']}")
    print("report:",path)

if __name__=="__main__":
    main()
