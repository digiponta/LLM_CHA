"""LLM_CHA v0.5.11: unverified teaching retrieval-first with provenance.

Never treats stored user testimony as verified fact or model-weight knowledge.
Distinct explanations for one concept are displayed together; this is a
difference/possible-conflict warning, not logical contradiction proof.
"""
from interactive_unknown_learning_v0510 import concept_from

def review(teacher,question):
    concept=concept_from(question)
    if not concept:return None
    records=teacher.lookup(concept)
    if not records:return None
    explanations=[]
    for index,record in enumerate(records,1):
        if record.get("status") not in ("PENDING_REVIEW","REVIEW_ACKNOWLEDGED") or record.get("train_ready") is not False:
            continue
        explanation=record.get("user_explanation")
        if not isinstance(explanation,str) or not explanation.strip():
            continue
        if explanation not in [e["text"] for e in explanations]:
            explanations.append({"text":explanation,"record_number":index,
                "source":record.get("source","unknown"),
                "truth_state":"USER_REPORTED_UNVERIFIED"})
    if not explanations:return None
    differing=len(explanations)>1
    contested=any(r.get("operational_status")=="CONTESTED" for r in records)
    if differing:
        lines=[f"「{concept}」について、以前教わった説明が{len(explanations)}件あります（いずれも未検証）。"]
        lines.extend(f"{i}. {x['text']}" for i,x in enumerate(explanations,1))
        lines.append("説明が異なるため、確認が必要です。自動的には確定しません。")
    else:
        lines=[f"以前「{concept}」について「{explanations[0]['text']}」と教えていただきました。この説明は未検証です。"]
    if contested:
        lines.insert(0,"注意：否定されたことのある知識です。再確認が必要です。")
    return {"concept":concept,"answer":"\n".join(lines),
        "records":explanations,"possible_conflict":differing,
        "truth_state":"USER_REPORTED_UNVERIFIED",
        "verified":False,"trusted_fact":False,"train_ready":False,
        "approved_for_sleep":False}
