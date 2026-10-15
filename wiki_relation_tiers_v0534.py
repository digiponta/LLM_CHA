"""v0.5.34 relation evidence tiers; no relation inferred from co-occurrence.

MEANS: source-backed structural/means description, not an explanation.
ENABLES / CAUSES: only explicit directional clauses in the source.
These are linguistic evidence classifications, not scientific verification.
"""
import re
from wiki_typed_propositions_v0532 import extract

ENABLE_PATTERNS=(r"(.+?)によって(.+?)が可能になる",r"(.+?)を用いることで(.+?)が可能になる")
CAUSE_PATTERNS=(r"(.+?)が原因で(.+?)が生じる",r"(.+?)に起因して(.+?)が生じる")

def classify(sentence,source=None):
    if not isinstance(sentence,str) or not sentence.strip():return []
    records=extract(sentence,source)
    output=[]
    for item in records:
        if item["type"] in ("STRUCTURE","COMPONENT"):
            output.append({"relation":"MEANS","subject":item["subject"],
                           "object":item["object"],"evidence_span":item["evidence_span"],
                           "source":source,"claim_strength":"STRUCTURAL_DESCRIPTION",
                           "verified":False,"train_ready":False,"promoted":False})
    for relation,patterns in (("ENABLES",ENABLE_PATTERNS),("CAUSES",CAUSE_PATTERNS)):
        for pattern in patterns:
            for m in re.finditer(pattern,sentence):
                left,right=m.group(1).strip(" 、。"),m.group(2).strip(" 、。")
                # Conservative: exclude complex/ambiguous multi-clause matches.
                if not left or not right or any(x in left+right for x in ("。","\n","しかし")):
                    continue
                output.append({"relation":relation,"subject":left,"object":right,
                               "evidence_span":m.group(0),"source":source,
                               "claim_strength":"EXPLICIT_LINGUISTIC_RELATION",
                               "verified":False,"train_ready":False,"promoted":False})
    return output

def assess_why(question,sentence,source=None):
    if not isinstance(question,str) or not any(w in question for w in ("なぜ","どうして","理由")):
        return {"status":"NOT_APPLICABLE","relations":[]}
    relations=classify(sentence,source)
    means=[r for r in relations if r["relation"]=="MEANS"]
    explicit=[r for r in relations if r["relation"] in ("ENABLES","CAUSES")]
    # Explicit linguistic relations are NOT automatically matched to a
    # specific question's target; do not promote to direct answers here.
    return {"status":"MEANS_PARTIAL" if means else "NO_RELATION_EVIDENCE",
            "relations":relations,"means_count":len(means),
            "explicit_direction_count":len(explicit),
            "causal_answer_approved":False,
            "verified":False,"train_ready":False}
