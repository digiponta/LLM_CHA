"""v0.5.45 paired baseline vs dual-gate fixture evaluation.

The fixture evidence is provided, not fetched. A supplied UNSUPPORTED assessment
is not ground truth that an answer is false.
"""
import json
from pathlib import Path
from answer_quality_gate_v0542 import evaluate
from dual_quality_gate_v0545 import decide
from wiki_answer_assessment_v0540 import assess

def evaluate_cases(cases):
    results=[]
    for item in cases:
        topic=item.get("topic")
        gen=evaluate(item["user"],item["original"],accepted=item["accepted"],
                     agreement=item.get("agreement"),wiki_topic=topic)
        # Compare only when an explicit, already-available evidence span is supplied.
        evidence_state=(assess(item["original"],item["evidence"],topic,
                          item.get("source","FIXTURE_EVIDENCE_UNVERIFIED"))["status"]
                        if item.get("evidence") else None)
        dual=decide(item["user"],item["original"],accepted=item["accepted"],
                    agreement=item.get("agreement"),topic=topic,
                    evidence_status=evidence_state)
        results.append({"id":item["id"],"needs_repair":bool(item["expected"]["needs_repair"]),
          "baseline_suggest":gen["suggest_wiki"],"dual_suggest":dual["suggest_wiki"],
          "generation_gate":dual["generation_gate"],"evidence_gate":dual["evidence_gate"],
          "dual_decision":dual["decision"],"reason":dual["reason"]})
    def cm(field):
        tp=sum(r["needs_repair"] and r[field] for r in results)
        fp=sum(not r["needs_repair"] and r[field] for r in results)
        fn=sum(r["needs_repair"] and not r[field] for r in results)
        tn=sum(not r["needs_repair"] and not r[field] for r in results)
        ratio=lambda x,y:round(x/y,4) if y else None
        return {"tp":tp,"fp":fp,"tn":tn,"fn":fn,
          "precision":ratio(tp,tp+fp),"recall":ratio(tp,tp+fn)}
    return {"version":"v0.5.45","evaluation":"FIXTURE_ONLY","baseline":cm("baseline_suggest"),
            "dual_gate":cm("dual_suggest"),"cases":results,"external_verification":False,
            "auto_lookup":False,"train_ready":False}

def main():
    path=Path(__file__).parent/"data"/"wiki_repair_eval_v0543.json"
    print(json.dumps(evaluate_cases(json.loads(path.read_text(encoding="utf-8"))["cases"]),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
