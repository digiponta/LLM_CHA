"""v0.5.39 explicit /wiki retry of a prior utterance, read-only evidence.

Does not claim to verify original model output, train, or auto-promote.
"""
import re
from wikipedia_acquisition_v0517 import lookup

def resolve_topic(utterance,explicit=None):
    if explicit:
        if not isinstance(explicit,str) or len(explicit.strip())>60:return None
        return explicit.strip()
    if not isinstance(utterance,str):return None
    for term in ("量子コンピュータ","超伝導量子干渉計","SQUID","量子センサー","人工知能","量子力学"):
        if term in utterance:return "超伝導量子干渉計" if term=="SQUID" else term
    return None

def retry(utterance,explicit=None,fetch=None):
    topic=resolve_topic(utterance,explicit)
    if not topic:
        return {"status":"TOPIC_UNRESOLVED","answer":"検索対象を特定できない。/wiki 検索語 を指定してほしい。"}
    evidence=lookup(topic,fetch=fetch,context=utterance)
    if evidence.get("status")!="FOUND":
        return {"status":"EVIDENCE_UNAVAILABLE","answer":"Wikipediaから回答に使える資料を取得できなかった。",
                "topic":topic,"lookup_status":evidence.get("status"),"verified":False,"train_ready":False}
    # Limit to exact sourced definitional sentence, with no inferred WHY.
    excerpt=evidence.get("extract","").strip()
    first=re.split(r"[。\n]",excerpt,maxsplit=1)[0].strip()
    if not 8<=len(first)<=300 or any(x in first for x in ("{{","}}")):
        return {"status":"EVIDENCE_INSUFFICIENT","answer":"取得した資料から短い根拠文を確認できなかった。",
                "topic":topic,"verified":False,"train_ready":False}
    return {"status":"EVIDENCE_FOUND","answer":"Wikipediaには「"+first+"。」と記載されている。元の回答はこの資料による確認を受けていない。",
            "topic":topic,"source":evidence["url"],"evidence_span":first,
            "route":"WIKIPEDIA_REPAIR","truth_state":"EXTERNAL_UNVERIFIED",
            "verified":False,"train_ready":False,"promoted":False}
