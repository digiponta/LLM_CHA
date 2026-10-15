"""v0.5.44 evaluation with separate repair-need, evidence availability and rendering.

All labels are small manually assigned FIXTURE labels. No online knowledge
verification, no semantic truth claims, and no training or promotion.
"""
import json
from pathlib import Path
from answer_quality_gate_v0542 import evaluate
from wiki_conversational_repair_v0541 import render

def evaluate_cases(cases):
    n={key:0 for key in ("total","need","no_need","tp","fp","tn","fn",
      "need_with_evidence","need_without_evidence","rendered","render_fail",
      "grounded","continuity","unknown_need","unknown_recovered")}
    details=[]
    for case in cases:
        required=bool(case["expected"]["needs_repair"])
        available=bool(case.get("evidence"))
        topic=case.get("topic")
        suggestion=evaluate(case["user"],case["original"],accepted=case["accepted"],
           agreement=case.get("agreement"),wiki_topic=topic)["suggest_wiki"]
        n["total"]+=1;n["need" if required else "no_need"]+=1
        n["tp" if required and suggestion else "fn" if required else "fp" if suggestion else "tn"]+=1
        wiki={"status":"EVIDENCE_FOUND","topic":topic,"evidence_span":case["evidence"],
              "source":case.get("source","https://example.org/fixture"),
              "verified":False,"train_ready":False,"promoted":False} if available else {"status":"EVIDENCE_UNAVAILABLE"}
        output=render(case["user"],wiki) if required and available else wiki
        grounded=bool(required and available and output.get("evidence_span")
             and output["evidence_span"] in output.get("answer","")
             and output.get("source")==wiki.get("source"))
        # Mechanical continuation proxy: a question about the same topic.
        continuity=bool(grounded and topic and topic in output.get("answer","") and "？" in output.get("answer",""))
        if required:
            n["need_with_evidence" if available else "need_without_evidence"]+=1
            if available:
                n["grounded"]+=int(grounded);n["continuity"]+=int(continuity)
                n["rendered" if grounded else "render_fail"]+=1
            if case["original"]=="未学習です":
                n["unknown_need"]+=1;n["unknown_recovered"]+=int(grounded)
        details.append({"id":case["id"],"need":required,"suggested":suggestion,
          "evidence_available":available,"evidence_preserved":grounded if required and available else None,
          "continuity_proxy":continuity if required and available else None,
          "render_status":("RENDERED" if grounded else "RENDER_FAILED") if required and available
                           else ("NO_EVIDENCE" if required else "NOT_NEEDED")})
    def div(a,b):
        return round(a/b,4) if b else None
    return {"version":"v0.5.44","evaluation":"FIXTURE_ONLY","counts":n,
      "metrics":{"suggestion_precision":div(n["tp"],n["tp"]+n["fp"]),
                 "suggestion_recall":div(n["tp"],n["tp"]+n["fn"]),
                 "suggestion_false_positive_rate":div(n["fp"],n["no_need"]),
                 "evidence_availability_rate":div(n["need_with_evidence"],n["need"]),
                 "render_success_given_evidence":div(n["rendered"],n["need_with_evidence"]),
                 "evidence_preservation_rate":div(n["grounded"],n["need_with_evidence"]),
                 "conversation_continuity_proxy":div(n["continuity"],n["need_with_evidence"]),
                 "unknown_recovery_given_need":div(n["unknown_recovered"],n["unknown_need"])},
      "details":details,"external_verification":False,"train_ready":False}

def main():
    fixture=Path(__file__).parent/"data"/"wiki_repair_eval_v0543.json"
    print(json.dumps(evaluate_cases(json.loads(fixture.read_text(encoding="utf-8"))["cases"]),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
