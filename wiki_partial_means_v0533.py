"""v0.5.33 partial means/structure answers to WHY, without causal claims."""
from wiki_typed_propositions_v0532 import extract

def partial_why(question,sentence,source=None):
    if not isinstance(question,str) or not any(t in question for t in ("なぜ","どうして","理由")):
        return {"status":"NOT_APPLICABLE","answer":None}
    if not any(t in question for t in ("高感度","感度が高","感度の高")):
        return {"status":"NOT_APPLICABLE","answer":None}
    records=extract(sentence,source)
    structure=next((x for x in records if x["type"]=="STRUCTURE"),None)
    component=next((x for x in records if x["type"]=="COMPONENT"),None)
    performance=next((x for x in records if x["type"]=="PERFORMANCE"),None)
    if not structure or not component or not performance or not source:
        return {"status":"INSUFFICIENT_PARTIAL_EVIDENCE","answer":None,"records":records}
    # The presence of both a structural description and high sensitivity
    # establishes co-description, not the direction or existence of a cause.
    answer=(f"資料には、{component['subject']}は{component['object']}を含む"
            f"{structure['object']}に基づくと記載されている。"
            "これは構造・手段についての部分的な説明であり、"
            "その構造が高感度を生む物理的な因果関係までは、この記述だけでは確認できない。")
    return {"status":"PARTIAL_MEANS_EVIDENCE","answer":answer,"records":[component,structure,performance],
            "source":source,"quality_gate":"STRUCTURE_NOT_CAUSAL",
            "verified":False,"train_ready":False,"promoted":False,"causal_explanation":False}
