"""Dynamic, source-anchored definition extraction. Research-only, exact quote gate."""
import re
from evidence_alias_binding_v013588262 import bind as prior_bind
from evidence_alias_normalization_v013588261 import canonical_subject, matches_subject
from evidence_conditioned_generation_v013588228 import evidence_gate
from question_aware_evidence_v013588255 import classify, split_sentences

HISTORICAL=re.compile(r"かつて|当時|従来|世紀|と考えられていた|学説|歴史|提唱|起源")
DEFINITION_END=re.compile(r"(?:である|を指す|という|のことである|を意味する|と呼ぶ|にあたる|を行う装置|を扱う理論)(?:。|$)")
DEFINITION_PREDICATE=re.compile(r"(?:とは|は、|は、?.{1,70}?を指す|は、?.{1,70}?を意味する)")
ALIASED_TITLE=("CPU","閃亜鉛鉱")

def subject_anchor(sentence,title):
    c=canonical_subject(title)
    if c in sentence:return True
    if c=="CPU" and "中央処理装置" in sentence:return True
    if c=="閃亜鉛鉱" and "スファレライト" in sentence:return True
    return False

def explicit_definition(sentence,title):
    s=sentence.strip()
    if not 15<=len(s)<=300:return False
    if HISTORICAL.search(s):return False
    if not subject_anchor(s,title):return False
    if not DEFINITION_END.search(s):return False
    # Prefer initial lead-style subject definitions, including pronunciation/English aliases.
    head=s[:110]
    c=canonical_subject(title)
    if not (c in head or (c=="CPU" and "中央処理装置" in head)):return False
    # A definitional copula must be present, not a consequence or an incidental mention.
    if not DEFINITION_PREDICATE.search(s):return False
    # Universe as a lexical translation requires separate sense disambiguation.
    if c=="宇宙" and ("訳語" in s or "単語" in s or "語源" in s):return False
    return True

def bind(question,evidence):
    if evidence.get("status")!="EVIDENCE":
        return {"question":question,"status":"ABSTAIN_NO_EVIDENCE"}
    title=str(evidence.get("topic",""))
    if not matches_subject(question,title,evidence.get("excerpt","")):
        return {"question":question,"status":"ABSTAIN_SUBJECT_MISMATCH"}
    if classify(question)!="definition":
        return prior_bind(question,evidence)
    # preserve known, stronger conservative patterns when they already work.
    old=prior_bind(question,evidence)
    if old["status"]=="BOUND_EXTRACT_ACCEPTED":return old
    # No fallback for explicitly historical cosmic claims from unrelated pages.
    for sentence in split_sentences(evidence.get("excerpt","")):
        if not explicit_definition(sentence,title):continue
        gate,_=evidence_gate(sentence,evidence)
        if gate!="ACCEPT_SOURCE_EXTRACT":continue
        return {"question":question,"status":"BOUND_EXTRACT_ACCEPTED",
                "subject":canonical_subject(title),"relation":"definition",
                "value":sentence,"sentence":sentence,"gate":gate,
                "method":"DYNAMIC_SOURCE_ANCHORED_DEFINITION",
                "source_trust":"EXTERNAL_UNVERIFIED",
                "answer":sentence+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}
    return {"question":question,"subject":canonical_subject(title),
            "relation":"definition","status":"ABSTAIN_NO_BOUND_EVIDENCE"}

def answer_or_abstain(question,evidence):
    r=bind(question,evidence)
    if r["status"]!="BOUND_EXTRACT_ACCEPTED":
        r["answer"]="提示された資料では、質問の対象・関係・回答値を確認できません。"
    return r
