"""Conservative explicit causal-role binding; baseline handles all other relations."""
import re
from evidence_definition_anaphora_v013588257 import bind as base_bind, subject_of
from question_aware_evidence_v013588255 import classify,split_sentences
from evidence_conditioned_generation_v013588228 import evidence_gate

CAUSE_PATTERN=re.compile(r"(?:宇宙(?:の)?膨張|宇宙が膨張する)(?:の)?原因は[、\s]*([^。]{2,100}?)(?:による|である|だと説明される|とされる|と説明される)(?:。|$)")
def cause_value(sentence,question):
    if subject_of(question)!="宇宙" or "膨張" not in question:return None
    match=CAUSE_PATTERN.search(sentence)
    if not match:return None
    value=match.group(1).strip(" 、")
    if not value or "原因" in value or len(value)<2:return None
    return value

def bind(question,evidence):
    if classify(question)!="cause":return base_bind(question,evidence)
    result={"question":question,"subject":subject_of(question),"relation":"cause",
            "source_trust":"EXTERNAL_UNVERIFIED"}
    if evidence.get("status")!="EVIDENCE":
        return {**result,"status":"ABSTAIN_NO_EVIDENCE"}
    if result["subject"]!="宇宙" or "膨張" not in question:
        return {**result,"status":"ABSTAIN_UNSUPPORTED_QUERY"}
    for sentence in split_sentences(evidence.get("excerpt","")):
        if not 15<=len(sentence)<=300:continue
        value=cause_value(sentence,question)
        if value is None:continue
        gate,_=evidence_gate(sentence,evidence)
        if gate!="ACCEPT_SOURCE_EXTRACT":continue
        return {**result,"status":"BOUND_EXTRACT_ACCEPTED","value":value,
                "sentence":sentence,"gate":gate,
                "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}
    return {**result,"status":"ABSTAIN_NO_BOUND_EVIDENCE"}

def answer_or_abstain(question,evidence):
    r=bind(question,evidence)
    if r["status"]!="BOUND_EXTRACT_ACCEPTED":
        r["answer"]="提示された資料では、質問の対象・関係・回答値を確認できません。"
    return r
