"""Conservative definition and temporal anaphora binding; offline research."""
import re
from evidence_conditioned_generation_v013588228 import evidence_gate
from question_aware_evidence_v013588255 import classify, split_sentences

SUBJECTS=("ビッグバン","宇宙","スファレライト")
HISTORY=re.compile(r"考え方|考えられ|とされた|信じられ|支配的|学説|世紀前半|定常的")
AGE=re.compile(r"(?:約|およそ|今から)?\s*\d+(?:\.\d+)?\s*億年(?:（[^）]{1,35}）)?\s*前")
def subject_of(question):
    return next((subject for subject in SUBJECTS if subject in question),None)

def definition_value(sentence,subject):
    if HISTORY.search(sentence):return None
    if subject=="宇宙":
        if sentence.startswith("ビッグバン"):return None
        if not re.search(r"宇宙とは|宇宙(?:は|という言葉は).{3,60}(?:を指す|の総称である|の全体である)",sentence):
            return None
    elif subject=="ビッグバン":
        if not re.search(r"ビッグバン.{0,25}とは",sentence):return None
    elif f"{subject}とは" not in sentence:return None
    return sentence

def antecedent_is_event(sentences,idx,subject):
    if idx==0:return False
    previous=sentences[idx-1]
    return subject in previous and bool(re.search(r"開始|膨張|起き|発生|時刻|時期|生まれ",previous))

def bind(question,evidence):
    relation=classify(question)
    subject=subject_of(question)
    result={"question":question,"subject":subject,"relation":relation,
            "source_trust":"EXTERNAL_UNVERIFIED"}
    if evidence.get("status")!="EVIDENCE":
        return {**result,"status":"ABSTAIN_NO_EVIDENCE"}
    if not subject or relation=="unknown":
        return {**result,"status":"ABSTAIN_UNSUPPORTED_QUERY"}
    sentences=split_sentences(evidence.get("excerpt",""))
    candidates=[]
    for idx,sentence in enumerate(sentences):
        if not 15<=len(sentence)<=300:continue
        if relation=="definition":
            value=definition_value(sentence,subject)
        elif relation=="time" and subject=="ビッグバン":
            match=AGE.search(sentence)
            if not match:continue
            if subject not in sentence:
                if not re.search(r"その時刻|その時期",sentence):continue
                if not antecedent_is_event(sentences,idx,subject):continue
            value=match.group().strip()
        elif relation=="composition":
            value=sentence if (subject in sentence and re.search(r"ZnS|硫化亜鉛|化学組成|組成は",sentence)) else None
        else:
            value=None
        if value is None:continue
        gate,_=evidence_gate(sentence,evidence)
        if gate!="ACCEPT_SOURCE_EXTRACT":continue
        candidates.append((1 if subject in sentence else 0,-idx,sentence,value))
    if not candidates:
        return {**result,"status":"ABSTAIN_NO_BOUND_EVIDENCE"}
    candidates.sort(reverse=True)
    _,_,sentence,value=candidates[0]
    return {**result,"status":"BOUND_EXTRACT_ACCEPTED","value":value,
            "sentence":sentence,"gate":"ACCEPT_SOURCE_EXTRACT",
            "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}

def answer_or_abstain(question,evidence):
    result=bind(question,evidence)
    if result["status"]!="BOUND_EXTRACT_ACCEPTED":
        result["answer"]="提示された資料では、質問の対象・関係・回答値を確認できません。"
    return result
