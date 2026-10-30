"""Conservative question/evidence subject, relation, value binding.

A lexical binding is not a semantic entailment proof. Unknown cases abstain.
"""
import re
from evidence_conditioned_generation_v013588228 import evidence_gate
from question_aware_evidence_v013588255 import classify,split_sentences

AGE=re.compile(r"(?:約|およそ|今から)?\s*\d+(?:\.\d+)?\s*億年(?:前)?")
SUBJECTS=("ビッグバン","宇宙","スファレライト")
def subject_of(question):
    q=str(question)
    for name in SUBJECTS:
        if name in q:return name
    return None

def relevant_subject(sentence,subject,relation):
    # Do not conflate cosmic expansion with a Big Bang event.
    if not subject:return False
    if subject=="ビッグバン":
        return bool(re.search(r"ビッグバン|その時刻|その時期",sentence))
    if subject=="宇宙":
        return "宇宙" in sentence and (relation!="definition" or "ビッグバンとは" not in sentence)
    return subject in sentence

def relation_value(sentence,relation,subject):
    s=str(sentence)
    if relation=="time" and subject=="ビッグバン":
        match=AGE.search(s)
        return match.group().strip() if match else None
    if relation=="definition":
        if subject=="宇宙":
            return s if re.search(r"宇宙とは|宇宙は.{0,24}(?:である|を指す|という)",s) and not s.startswith("ビッグバン") else None
        if subject=="ビッグバン":
            return s if re.search(r"ビッグバン.{0,24}とは",s) else None
        return s if f"{subject}とは" in s else None
    if relation=="composition":
        return s if re.search(r"ZnS|硫化亜鉛|化学組成|組成は",s) else None
    # Causal / mechanism phrases need validated event-role semantics, not a bare conjunction.
    return None

def bind(question,evidence):
    relation=classify(question)
    subject=subject_of(question)
    out={"question":question,"subject":subject,"relation":relation,
         "source_trust":"EXTERNAL_UNVERIFIED"}
    if evidence.get("status")!="EVIDENCE":
        return {**out,"status":"ABSTAIN_NO_EVIDENCE"}
    if relation=="unknown" or subject is None:
        return {**out,"status":"ABSTAIN_UNSUPPORTED_QUERY"}
    eligible=[]
    for idx,s in enumerate(split_sentences(evidence.get("excerpt",""))):
        if len(s)>300 or len(s)<15:continue
        if not relevant_subject(s,subject,relation):continue
        value=relation_value(s,relation,subject)
        if value is None:continue
        gate,_=evidence_gate(s,evidence)
        if gate!="ACCEPT_SOURCE_EXTRACT":continue
        # Explicit subject has priority over local anaphora.
        priority=1 if subject in s else 0
        eligible.append((priority,-idx,s,value))
    if not eligible:
        return {**out,"status":"ABSTAIN_NO_BOUND_EVIDENCE"}
    eligible.sort(reverse=True)
    _,_,sentence,value=eligible[0]
    return {**out,"status":"BOUND_EXTRACT_ACCEPTED","value":value,
            "sentence":sentence,"gate":"ACCEPT_SOURCE_EXTRACT",
            "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}

def answer_or_abstain(question,evidence):
    result=bind(question,evidence)
    if result["status"]!="BOUND_EXTRACT_ACCEPTED":
        result["answer"]="提示された資料では、質問の対象・関係・回答値を確認できません。"
    return result
