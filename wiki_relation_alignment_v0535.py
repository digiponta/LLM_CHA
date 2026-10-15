"""v0.5.35 question-target alignment for explicitly directional relations.

Limited SQUID sensitivity questions. Direction and topical alignment are
necessary but not sufficient for a scientifically verified causal claim.
"""
from wiki_relation_tiers_v0534 import classify

SENSITIVITY=("高感度","感度が高","感度の高","磁場感度","感度向上","感度が向上","感度を向上")
DOWNSTREAM=("MRI","撮像","診断","医用画像","実用化")
PHYSICS=("ジョセフソン","超伝導","量子干渉","磁束","回路")
SUBJECT=("SQUID","超伝導量子干渉計")

def align(question,sentence,source=None):
    if not isinstance(question,str) or not isinstance(sentence,str):
        return {"status":"INVALID_INPUT","candidates":[]}
    if not any(x in question for x in ("なぜ","どうして","理由")) or not any(x in question for x in SENSITIVITY):
        return {"status":"NOT_APPLICABLE","candidates":[]}
    rows=[]
    for relation in classify(sentence,source):
        if relation["relation"] not in ("ENABLES","CAUSES"):continue
        cause,effect=relation["subject"],relation["object"]
        # No match from unrelated effects, regardless of an explicit link.
        if any(x in effect for x in DOWNSTREAM):
            reason="DOWNSTREAM_EFFECT_NOT_SENSITIVITY"
        elif not any(x in effect for x in SENSITIVITY):
            reason="TARGET_EFFECT_MISMATCH"
        elif not any(x in cause for x in PHYSICS):
            reason="CAUSE_NOT_GROUNDED_IN_DEVICE"
        elif not any(x in sentence for x in SUBJECT):
            reason="SUBJECT_NOT_GROUNDED"
        else:
            reason="DIRECTION_AND_TARGET_ALIGNED"
        rows.append({**relation,"aligned":reason=="DIRECTION_AND_TARGET_ALIGNED","reason":reason})
    matched=[x for x in rows if x["aligned"]]
    return {"status":"ALIGNED_CANDIDATE" if matched else "NO_ALIGNED_CAUSAL_EVIDENCE",
            "candidates":rows,"aligned_count":len(matched),
            "causal_answer_approved":False,"verified":False,"train_ready":False}
