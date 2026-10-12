"""v0.3.4 multi-important-topic competition evaluation (synthetic).

Compare fixed-budget Hybrid and protected Auto-Pin on independently authored
trace families. Query metrics measure cache membership, not semantic validity.
"""
import json
from pathlib import Path
from adaptive_retention_eval_v023351 import Event
from hybrid_retention_v0310 import hybrid
from auto_pin_protection_v0330 import evaluate as protected

def traces():
    def observe(name,important=False): return Event("observe",name,important)
    def query(name,important=True): return Event("query",name,important)
    return {
        "old_vs_new":[observe("旧A",True),observe("旧B",True)]
            +[observe(f"一時{i}") for i in range(9)]
            +[observe("新A",True),observe("新B",True)]
            +[query("旧A"),query("旧B"),query("新A"),query("新B")],
        "recent_vs_stale":[observe("旧A",True),observe("旧B",True)]
            +[observe("旧A"),observe("旧B")]
            +[observe("新A",True),query("旧A"),query("旧B"),query("新A")],
        "frequency_competition":[observe("常連",True)]*8
            +[observe("旧B",True)]
            +[observe(f"雑談{i}") for i in range(9)]
            +[observe("新A",True)]
            +[query("常連"),query("旧B"),query("新A")],
        "revisit_after_reallocation":[observe("旧A",True),observe("旧B",True)]
            +[observe(f"一時{i}") for i in range(10)]
            +[observe("新A",True),query("旧A"),query("新A"),
              observe("旧A",True),query("旧A"),query("新A")],
        "explicit_protection":[observe("指定",True),observe("旧A",True)]
            +[observe(f"一時{i}") for i in range(10)]
            +[observe("新A",True),query("指定"),query("旧A"),query("新A")],
    }

def run(capacities=(2,4,8),age_thresholds=(4,8,16)):
    rows=[]
    for name,events in traces().items():
        for capacity in capacities:
            base=hybrid(events,capacity)
            rows.append({"scenario":name,"events":len(events),**base})
            for age in age_thresholds:
                # Explicit protection only when explicitly provided as scenario constraint.
                explicit=("指定",) if name=="explicit_protection" else ()
                result=protected(events,capacity,explicit_topics=explicit,
                                 min_age_for_reallocation=age)
                rows.append({"scenario":name,"events":len(events),
                             "min_age_for_reallocation":age,**result})
    return {"version":"v0.3.4","scenarios":len(traces()),"rows":rows,
            "limitations":"synthetic observations, labels and read-only queries; no chat runtime or GPU scoring"}

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",default="results/important_competition_v0340.json")
    args=parser.parse_args()
    result=run()
    path=Path(args.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("v0.3.4 scenarios=",result["scenarios"],"rows=",len(result["rows"]))
    for row in result["rows"]:
        if row["policy"]=="protected_auto_pin_v033":
            print(row["scenario"],"capacity=",row["capacity"],
                  "age=",row["min_age_for_reallocation"],
                  "important=",row["important_retention_rate"],
                  "demotions=",row["auto_demotions"],
                  "refusals=",row["protected_insertion_refusals"])
    print("report:",path)

if __name__=="__main__":
    main()
