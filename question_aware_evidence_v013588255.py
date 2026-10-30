"""Question-aware source-extractive answering: explicit attribute routing and abstention.

An exact copied source sentence is not equivalent to verified factual truth.
"""
import re
from evidence_conditioned_generation_v013588228 import evidence_gate

ATTRIBUTE_PATTERNS={
 "time":(r"いつ|何年|何億年前|時期|年代",r"年|時刻|億年前|世紀"),
 "cause":(r"なぜ|どうして|理由|原因",r"ため|原因|によって|理由|結果|従って"),
 "mechanism":(r"どのように|どうやって|仕組み|メカニズム",r"によって|により|過程|仕組み|観測"),
 "composition":(r"成分|化学組成|何から|組成",r"組成|元素|硫化|ZnS|成分"),
 "definition":(r"とは|何ですか|説明|概要",r"とは|である|という|指す"),
}
DEFAULT_STOP={"とは","について","ください","教えて","知りたい","もっと","詳しく","説明","です","ます","何"}
def classify(question):
 q=str(question or "").strip()
 for label,(question_pattern,_) in ATTRIBUTE_PATTERNS.items():
  if re.search(question_pattern,q):return label
 return "unknown"

def keywords(text):
 parts=re.findall(r"[一-龥ぁ-んァ-ヶA-Za-z0-9]{2,}",str(text or ""))
 return {t for t in parts if t not in DEFAULT_STOP}

def split_sentences(excerpt):
 return [s.strip() for s in re.split(r"(?<=。)",str(excerpt or "")) if s.strip()]

def select_for_question(question,evidence,max_chars=300):
 attribute=classify(question)
 base={"question":question,"attribute":attribute,"source_trust":"EXTERNAL_UNVERIFIED"}
 if evidence.get("status")!="EVIDENCE":
  return {**base,"status":"ABSTAIN_NO_EVIDENCE","sentence":None,"score":0}
 if attribute=="unknown":
  return {**base,"status":"ABSTAIN_UNSUPPORTED_QUESTION","sentence":None,"score":0}
 excerpt=str(evidence.get("excerpt",""))
 qwords=keywords(question)
 ranked=[]
 for idx,sentence in enumerate(split_sentences(excerpt)):
  if not (15<=len(sentence)<=max_chars):continue
  if sentence.rstrip("。") not in excerpt:continue
  attribute_match=bool(re.search(ATTRIBUTE_PATTERNS[attribute][1],sentence))
  if not attribute_match:continue
  overlap=len(qwords & keywords(sentence))
  topic=str(evidence.get("topic","")).strip()
  topic_match=bool(topic and topic in sentence)
  score=10+3*overlap+(2 if topic_match else 0)
  # Only an explicit attribute signal is sufficient; never infer causation from chronology alone.
  ranked.append((score,-idx,sentence))
 if not ranked:return {**base,"status":"ABSTAIN_NO_MATCHING_ATTRIBUTE","sentence":None,"score":0}
 ranked.sort(reverse=True)
 score,_,sentence=ranked[0]
 gate,_=evidence_gate(sentence,evidence)
 if gate!="ACCEPT_SOURCE_EXTRACT":
  return {**base,"status":"ABSTAIN_GATE_REJECTED","sentence":None,"score":score,"gate":gate}
 return {**base,"status":"EXTRACT_ACCEPTED","sentence":sentence,"score":score,
         "gate":gate,"source_url":evidence.get("url",""),
         "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}

def answer_or_abstain(question,evidence):
 r=select_for_question(question,evidence)
 if r["status"]!="EXTRACT_ACCEPTED":
  return {**r,"answer":"提示された根拠資料だけでは、この質問への回答を確認できません。"}
 return r
