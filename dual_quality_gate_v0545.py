"""v0.5.45 dual gate. Read-only: never fetches sources or changes model acceptance.

Evidence support must originate in an existing, explicitly supplied comparison.
UNSUPPORTED means absence of support, not factual contradiction.
"""
from answer_quality_gate_v0542 import evaluate

VALID={"SUPPORTED","CONTRADICTED","UNSUPPORTED","INSUFFICIENT"}

def decide(user,answer,*,accepted,agreement=None,topic=None,evidence_status=None):
    generation=evaluate(user,answer,accepted=accepted,agreement=agreement,wiki_topic=topic)
    if evidence_status not in VALID:
        evidence="NOT_CHECKED"
    else:
        evidence=evidence_status
    if generation["status"]=="REVIEW":
        decision="REVIEW"
        reason="GENERATION_REVIEW"
    elif evidence=="CONTRADICTED":
        decision="REVIEW"
        reason="EXPLICIT_CONFLICT_CANDIDATE"
    elif evidence=="UNSUPPORTED":
        decision="EVIDENCE_NEEDED"
        reason="NO_MATCHING_EVIDENCE"
    elif evidence=="INSUFFICIENT":
        decision="ACCEPT"
        reason="COMPARISON_INCONCLUSIVE_NO_OVERRIDE"
    elif evidence=="SUPPORTED":
        decision="ACCEPT"
        reason="ATOMIC_EVIDENCE_MATCH"
    elif generation["status"]=="NO_WIKI_TOPIC":
        decision="ACCEPT"
        reason="NO_WIKI_TOPIC_OR_EVIDENCE"
    else:
        decision="ACCEPT"
        reason="GENERATION_ONLY_NO_EVIDENCE_CHECK"
    return {"decision":decision,"reason":reason,"generation_gate":generation["status"],
            "evidence_gate":evidence,"suggest_wiki":bool(topic and decision!="ACCEPT"),
            "evidence_checked":evidence!="NOT_CHECKED",
            "verified":False,"train_ready":False,"auto_lookup":False,"auto_promote":False}
