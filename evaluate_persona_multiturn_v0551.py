"""v0.5.51 persona multi-turn route evaluation, not a model benchmark.

Template routing and model output are separate cohorts. Model records must be
supplied explicitly and are never synthesized from template responses.
"""
import argparse
import json
from pathlib import Path
from persona_context_v0550 import PersonaContext

def evaluate_scenarios(scenarios):
    cases=[]
    for scenario in scenarios:
        controller=PersonaContext(scenario.get("persona","nagato"))
        turns=[]
        for t in scenario["turns"]:
            out=controller.handle(t["user"])
            expected=t.get("expected_route")
            observed=out["route"] if out else "DELEGATE"
            route_ok=observed==expected
            topic_ok=(True if "expected_topic" not in t else
                      bool(out and out.get("context_topic")==t["expected_topic"]))
            persona_ok=(True if out is None else out["persona"]==controller.persona)
            safe=(True if out is None else
                  out.get("knowledge_asserted") is False and
                  out.get("train_ready") is False and
                  out.get("auto_lookup") is False and out.get("auto_promote") is False)
            turns.append({"user":t["user"],"observed_route":observed,
                          "expected_route":expected,"route_ok":route_ok,
                          "topic_ok":topic_ok,"persona_ok":persona_ok,"safe":safe})
        cases.append({"id":scenario["id"],"persona":controller.persona,"turns":turns})
    rows=[t for case in cases for t in case["turns"]]
    ratio=lambda count:round(count/len(rows),4) if rows else None
    return {"evaluation":"TEMPLATE_ROUTER_ONLY","scenario_count":len(cases),
            "turns":len(rows),"route_accuracy":ratio(sum(t["route_ok"] for t in rows)),
            "topic_retention_proxy":ratio(sum(t["topic_ok"] for t in rows)),
            "persona_identity_consistency":ratio(sum(t["persona_ok"] for t in rows)),
            "safety_invariant_rate":ratio(sum(t["safe"] for t in rows)),
            "cases":cases}

def evaluate_model_records(records):
    # We cannot infer authentic persona or correctness from model text alone.
    # Explicit annotations are optional; unlabelled examples are unscored.
    rows=[]
    for r in records:
        if r.get("origin")!="MODEL_GENERATION":
            raise ValueError("model records require origin=MODEL_GENERATION")
        if not isinstance(r.get("reply"),str) or not r["reply"].strip():
            raise ValueError("model reply required")
        label=r.get("persona_consistent")
        if label is not None and not isinstance(label,bool):
            raise ValueError("persona_consistent must be boolean or null")
        rows.append({"id":r.get("id"),"checkpoint":r.get("checkpoint"),
                     "persona":r.get("persona"),"human_persona_label":label})
    labeled=[r["human_persona_label"] for r in rows if r["human_persona_label"] is not None]
    return {"evaluation":"MODEL_OUTPUT_ANNOTATION_ONLY","total":len(rows),
            "human_labeled":len(labeled),
            "human_label_agreement_rate":round(sum(labeled)/len(labeled),4) if labeled else None,
            "model_generated_here":False,"external_verification":False,"cases":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/persona_multiturn_eval_v0551.json")
    p.add_argument("--model-records",help="optional annotated real model outputs as JSON cases")
    p.add_argument("--output")
    args=p.parse_args()
    scenarios=json.loads(Path(args.input).read_text(encoding="utf-8"))["scenarios"]
    report={"version":"v0.5.51","router":evaluate_scenarios(scenarios),
            "model":None,"train_ready":False,"auto_lookup":False}
    if args.model_records:
        report["model"]=evaluate_model_records(json.loads(Path(args.model_records).read_text(encoding="utf-8"))["cases"])
    data=json.dumps(report,ensure_ascii=False,indent=2)
    print(data)
    if args.output:
        path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(data+"\n",encoding="utf-8")

if __name__=="__main__":main()
