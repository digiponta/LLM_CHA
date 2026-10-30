"""Alias-aware relation binding, isolated from production GUI.

Only adopts source-exact spans. Normalization is labeled as derived metadata.
"""
import re
from evidence_cause_binding_v013588259 import bind as legacy_bind
from evidence_alias_normalization_v013588261 import canonical_subject,composition_value,matches_subject
from question_aware_evidence_v013588255 import classify,split_sentences
from evidence_conditioned_generation_v013588228 import evidence_gate

def bind(question,evidence):
    if evidence.get("status")!="EVIDENCE":
        return {"question":question,"status":"ABSTAIN_NO_EVIDENCE"}
    title=str(evidence.get("topic",""))
    if not matches_subject(question,title,evidence.get("excerpt","")):
        return {"question":question,"status":"ABSTAIN_SUBJECT_MISMATCH",
                "subject":canonical_subject(title)}
    relation=classify(question)
    if relation=="composition" and canonical_subject(title) in ("閃亜鉛鉱","水"):
        sentences=split_sentences(evidence.get("excerpt",""))
        for sentence in sentences:
            if len(sentence.strip())<15 or len(sentence)>300:continue
            # Require explicit subject in the sentence, or a subject-anchored
            # property clause in a source whose title matches the question.
            if not (canonical_subject(title) in sentence or
                    re.search(r"(?:成分は|化学式\s*H2O|化学組成は)",sentence)):
                continue
            composition=composition_value(title,sentence)
            if not composition:continue
            gate,_=evidence_gate(sentence,evidence)
            if gate!="ACCEPT_SOURCE_EXTRACT":continue
            return {"question":question,"status":"BOUND_EXTRACT_ACCEPTED",
                    "subject":canonical_subject(title),"relation":"composition",
                    "value":composition["canonical_value"],
                    "surface_value":composition["surface_value"],
                    "normalization":"EXPLICIT_SURFACE_ALIAS",
                    "sentence":sentence,"gate":gate,"source_trust":"EXTERNAL_UNVERIFIED",
                    "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}
        return {"question":question,"subject":canonical_subject(title),
                "relation":"composition","status":"ABSTAIN_NO_BOUND_EVIDENCE"}
    if relation=="definition" and canonical_subject(title)=="CPU":
        for sentence in split_sentences(evidence.get("excerpt","")):
            if not 15<=len(sentence)<=300:continue
            if not ("CPU" in sentence and ("中央処理装置" in sentence or "コンピュータ" in sentence)):continue
            if not re.search(r"は、.{4,}(?:装置|プロセッサ)(?:である)?(?:。|$)",sentence):continue
            gate,_=evidence_gate(sentence,evidence)
            if gate=="ACCEPT_SOURCE_EXTRACT":
                return {"question":question,"status":"BOUND_EXTRACT_ACCEPTED","subject":"CPU",
                        "relation":"definition","value":sentence,"sentence":sentence,"gate":gate,
                        "source_trust":"EXTERNAL_UNVERIFIED",
                        "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}
        return {"question":question,"status":"ABSTAIN_NO_BOUND_EVIDENCE",
                "subject":"CPU","relation":"definition"}
    return legacy_bind(question,evidence)

def answer_or_abstain(question,evidence):
    result=bind(question,evidence)
    if result["status"]!="BOUND_EXTRACT_ACCEPTED":
        result["answer"]="提示された資料では、質問の対象・関係・回答値を確認できません。"
    return result
