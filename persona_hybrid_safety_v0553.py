"""v0.5.53 offline Hybrid safety gate.

Never treat unchecked raw LLM text as approved just because the
conversation controller delegates. A trusted runtime decision must explicitly
mark a non-knowledge response accepted; knowledge queries require separately
verified evidence. No training or external lookup.
"""
import re

def knowledge_query(user):
    if not isinstance(user,str):return False
    return bool(re.search(r"(?:とは[？?]?$|って何|教えて|説明して|なぜ|どうして|何ですか|[？?]$)",user.strip()))

def assess_raw(reply):
    if not isinstance(reply,str) or not reply.strip():
        return {"status":"REJECT","reason":"EMPTY"}
    text=reply.strip()
    if len(text)<6 or text.startswith(("、","。","の前身")):
        return {"status":"REVIEW","reason":"FRAGMENT"}
    if re.search(r"([^。、\s]{2,12})(?:、?\1){2,}",text):
        return {"status":"REVIEW","reason":"REPETITION"}
    return {"status":"UNVERIFIED","reason":"AUTOMATIC_QUALITY_NOT_PROVEN"}

def decide(row,*,runtime_accepted=False,evidence_verified=False):
    ctrl=row.get("controller") or {}
    raw=row.get("raw_llm") or {}
    reply=ctrl.get("reply")
    if isinstance(reply,str) and reply.strip():
        return {"reply":reply,"selected":"CONTROLLER","decision":"PRESENTATION_ONLY",
                "train_ready":False,"promoted":False}
    q=knowledge_query(row.get("user",""))
    assessment=assess_raw(raw.get("reply"))
    if q:
        # A lexical/fluency heuristic is never proof of factual correctness.
        if not evidence_verified:
            return {"reply":None,"selected":"KNOWLEDGE_GATE_REQUIRED",
                    "decision":"BLOCK_UNVERIFIED_KNOWLEDGE","raw_quality":assessment,
                    "train_ready":False,"promoted":False}
        return {"reply":None,"selected":"EXTERNAL_VERIFIED_RETRIEVAL_REQUIRED",
                "decision":"DEFER_TO_KNOWLEDGE_RUNTIME","raw_quality":assessment,
                "train_ready":False,"promoted":False}
    if runtime_accepted and assessment["status"]=="UNVERIFIED":
        return {"reply":raw["reply"],"selected":"RAW_RUNTIME_ACCEPTED",
                "decision":"ACCEPT_BY_TRUSTED_RUNTIME","raw_quality":assessment,
                "train_ready":False,"promoted":False}
    return {"reply":None,"selected":"RUNTIME_GATE_REQUIRED",
            "decision":"BLOCK_UNASSESSED_RAW","raw_quality":assessment,
            "train_ready":False,"promoted":False}
