"""v0.6.33 conservative response-quality gate.

Only exact reviewed answers or explicitly allowed full-sentence patterns are
accepted. This is a narrow regression gate, not general semantic evaluation.
"""
import re

REFERENCE_ANSWERS={
    "identity": ("長門有希。","長門有希","あなた => 長門有希"),
    "greeting": ("こんばんは。","こんばんは","こんばんは。お疲れ様","こんばんは。お疲れ様。"),
    "cat": ("猫","ネコ","ねこ","猫は動物です。","猫は哺乳類です。"),
}
def response_quality(answer, case):
    value=answer.strip()
    if not value:
        return {"pass":False,"reason":"EMPTY"}
    references=case.get("acceptable_answers", REFERENCE_ANSWERS.get(case["id"], ()))
    if not references:
        return {"pass":False,"reason":"NO_REVIEWED_REFERENCE"}
    if value in references:
        return {"pass":True,"reason":"REVIEWED_EXACT"}
    for pattern in case.get("acceptable_fullmatch_patterns",()):
        if re.fullmatch(pattern,value):
            return {"pass":True,"reason":"REVIEWED_PATTERN"}
    return {"pass":False,"reason":"NOT_REVIEWED_ACCEPTABLE"}

def gate_quality_report(previous, cases):
    answers=previous.get("answers",{})
    before=answers.get("before",{})
    after=answers.get("after",{})
    details=[]
    for case in cases:
        key=case["id"]
        b=response_quality(before.get(key,""),case)
        a=response_quality(after.get(key,""),case)
        details.append({"id":key,"group":case["group"],"before":b,"after":a,
                        "regression":b["pass"] and not a["pass"]})
    regressions=[r["id"] for r in details if r["regression"]]
    failed_after=[r["id"] for r in details if not r["after"]["pass"]]
    return {"pass":not failed_after and not regressions,
            "quality_failures":failed_after,"quality_regressions":regressions,
            "details":details,
            "limitations":"Only manually reviewed exact or fullmatch reference answers; not general semantics."}
