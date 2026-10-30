"""Auditable extractive evidence decoding: never invent or paraphrase facts.

This is an alternative to a rejected raw LLM candidate, not a semantic truth verifier.
"""
import re
from evidence_conditioned_generation_v013588228 import evidence_gate, verified_fallback

def sentences(text):
    return [x.strip() for x in re.split(r"(?<=。)",str(text or "")) if x.strip()]

def select_extract(evidence,max_chars=240,max_sentences=2):
    if evidence.get("status")!="EVIDENCE":
        return {"status":"NO_EVIDENCE","candidate":None,"gate":"NO_EVIDENCE","source":"NONE"}
    excerpt=str(evidence.get("excerpt",""))
    if not excerpt.strip():
        return {"status":"EMPTY_EXCERPT","candidate":None,"gate":"NO_EVIDENCE","source":"NONE"}
    # Only copy exact sentence spans, never add unsupported claims.
    candidates=[]
    for sentence in sentences(excerpt):
        span=sentence.strip()
        if 15<=len(span)<=max_chars and span.rstrip("。") in excerpt:
            candidates.append(span)
    for start in range(len(candidates)):
        group=[]
        for sentence in candidates[start:start+max_sentences]:
            if len("".join(group))+len(sentence)>max_chars:break
            group.append(sentence)
            candidate="".join(group)
            gate,_=evidence_gate(candidate,evidence)
            if gate=="ACCEPT_SOURCE_EXTRACT":
                return {"status":"EXTRACT_ACCEPTED","candidate":candidate,
                        "gate":gate,"source":"EVIDENCE_EXACT_SPAN",
                        "sentence_count":len(group)}
    return {"status":"NO_SAFE_EXTRACT","candidate":None,
            "gate":"REJECT_NOT_ENTAILED","source":"NONE"}

def evaluate_decoding(raw_candidate,evidence):
    raw_gate,_=evidence_gate(raw_candidate,evidence)
    extracted=select_extract(evidence)
    if raw_gate=="ACCEPT_SOURCE_EXTRACT":
        chosen=raw_candidate
        strategy="RAW_ACCEPTED"
    elif extracted["candidate"] is not None:
        chosen=extracted["candidate"]
        strategy="EXTRACTIVE_FALLBACK"
    else:
        return {"strategy":"ATTRIBUTED_FALLBACK","raw_gate":raw_gate,
                "extract_status":extracted["status"],
                "answer":verified_fallback(evidence),"gate":"NO_EXTRACT"}
    # The source is external and not independently verified.
    return {"strategy":strategy,"raw_gate":raw_gate,
            "extract_status":extracted["status"],"gate":"ACCEPT_SOURCE_EXTRACT",
            "answer":chosen+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}

