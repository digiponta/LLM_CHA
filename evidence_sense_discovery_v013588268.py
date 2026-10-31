"""Read-only evidence-driven sense candidate discovery (NOT approval).

Extract source-exact definitional statements, create deterministic candidate IDs,
and flag possible duplicates/conflicts. No writes, learning, or live promotion.
"""
import hashlib
import re
from question_aware_evidence_v013588255 import split_sentences
from evidence_conditioned_generation_v013588228 import evidence_gate

PATTERN=re.compile(r"(?P<term>[一-龥ぁ-んァ-ヶA-Za-z0-9・]{2,24})(?:（[^）]{1,70}）)?(?:とは|は、)(?P<meaning>[^。]{6,230})(?:。|$)")
HISTORY=re.compile(r"かつて|当時|と考えられていた|歴史的|という説があった")
def discover(evidence,known=()):
    if evidence.get("status")!="EVIDENCE":return []
    found=[]
    topic=str(evidence.get("topic","")).strip()
    for sentence in split_sentences(evidence.get("excerpt","")):
        if not 15<=len(sentence)<=300 or HISTORY.search(sentence):continue
        if evidence_gate(sentence,evidence)[0]!="ACCEPT_SOURCE_EXTRACT":continue
        for match in PATTERN.finditer(sentence):
            subject=match.group("term")
            # The source title must anchor the phrase; avoid mining incidental other subjects.
            if not topic or subject not in topic and topic not in subject:continue
            meaning=match.group("meaning").strip()
            if not re.search(r"である|を指す|意味する|のこと|現象|理論|分野|装置|化合物|エネルギー|能力",meaning):continue
            digest=hashlib.sha256((subject+"\n"+meaning).encode("utf-8")).hexdigest()[:16]
            overlaps=[k for k in known if k.get("subject")==subject and k.get("meaning")==meaning]
            conflicts=[k for k in known if k.get("subject")==subject and k.get("meaning")!=meaning]
            state="POSSIBLE_DUPLICATE" if overlaps else "POSSIBLE_CONFLICT" if conflicts else "PENDING_HUMAN_REVIEW"
            found.append({"id":"sense-"+digest,"subject":subject,"relation":"definition",
                          "meaning":meaning,"evidence_sentence":sentence,"source_topic":topic,
                          "source_url":str(evidence.get("url","")),"source_trust":"EXTERNAL_UNVERIFIED",
                          "review_status":state,"approved":False,"auto_promote":False,
                          "conflicting_ids":[k.get("id","") for k in conflicts]})
    return list({x["id"]:x for x in found}.values())

def inspect_snapshot(data,known=()):
    rows=[]
    for case in data.get("cases",[]):
        for candidate in discover(case.get("evidence",{}),known):
            rows.append({**candidate,"source_case_id":case.get("id")})
    return {"status":"SENSE_DISCOVERY_DIAGNOSTIC","candidates":rows,
            "candidate_count":len(rows),"approved_count":0,"production_changed":False}
