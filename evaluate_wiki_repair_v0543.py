"""v0.5.43: deterministic, fixture-only wiki repair evaluation.

These metrics measure behavior against fixture labels, NOT factual correctness
of Wikipedia, model accuracy in the wild, or generalization performance.
"""
from collections import Counter
import json
from pathlib import Path
from answer_quality_gate_v0542 import evaluate
from wiki_conversational_repair_v0541 import render
from wiki_answer_assessment_v0540 import assess

def evaluate_cases(cases):
    counts=Counter()
    details=[]
    for case in cases:
        expected=case["expected"]
        topic=case.get("topic")
        gate=evaluate(case["user"],case["original"],accepted=case["accepted"],
                      agreement=case.get("agreement"),wiki_topic=topic)
        suggested=gate["suggest_wiki"]
        eligible=bool(case.get("evidence"))
        wiki={"status":"EVIDENCE_FOUND","topic":topic,"evidence_span":case["evidence"],
              "source":case.get("source","https://example.org/fixture"),
              "verified":False,"train_ready":False,"promoted":False} if eligible else {"status":"EVIDENCE_UNAVAILABLE"}
        repaired=render(case["user"],wiki)
        comparison=assess(case["original"],case.get("evidence",""),topic,wiki.get("source"))
        grounded=(not eligible or (repaired.get("evidence_span","") in repaired.get("answer","")
                         and repaired.get("source")==wiki.get("source")))
        continuity=(not eligible or (topic in repaired.get("answer","") and
                     ("？" in repaired.get("answer",""))))
        recovered=bool(eligible and case["original"]=="未学習です" and grounded and continuity)
        success=bool(eligible and grounded and continuity and comparison["status"] in
                     ("SUPPORTED","CONTRADICTED","UNSUPPORTED","INSUFFICIENT"))
        unnecessary=bool(suggested and not expected["needs_repair"])
        counts["total"]+=1
        counts["eligible"]+=int(eligible)
        counts["repair_success"]+=int(success)
        counts["grounded"]+=int(eligible and grounded)
        counts["continuity"]+=int(eligible and continuity)
        counts["unknown_total"]+=int(case["original"]=="未学習です")
        counts["unknown_recovered"]+=int(recovered)
        counts["suggested"]+=int(suggested)
        counts["unnecessary_suggestions"]+=int(unnecessary)
        details.append({"id":case["id"],"gate":gate["status"],"assessment":comparison["status"],
                        "suggested":suggested,"expected_repair":expected["needs_repair"],
                        "repair_rendered":success,"evidence_preserved":grounded if eligible else None,
                        "continuity":continuity if eligible else None,
                        "unknown_recovered":recovered,"truth_verified":False})
    def rate(num,den):
        return round(counts[num]/counts[den],4) if counts[den] else None
    return {"version":"v0.5.43","evaluation":"FIXTURE_ONLY","counts":dict(counts),
            "rates":{"repair_success_rate":rate("repair_success","eligible"),
                     "evidence_grounding_rate":rate("grounded","eligible"),
                     "conversation_continuity_rate":rate("continuity","eligible"),
                     "false_suggestion_rate":rate("unnecessary_suggestions","total"),
                     "unknown_recovery_rate":rate("unknown_recovered","unknown_total")},
            "details":details,"external_verification":False,"train_ready":False}

def main():
    path=Path(__file__).parent/"data"/"wiki_repair_eval_v0543.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_cases(data["cases"]),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
