"""Read-only, source-attributed Nagato corpus evidence for explicit topic QA.

This adds *context*, not an approved factual definition. No auto-promote.
"""
import re
from pathlib import Path
from corpus_role_classifier_v0942 import rank_mentions
from question_aware_evidence_v0943 import select_evidence

def corpus_mentions(topic, corpus, max_items=2):
    topic=str(topic or "").strip()
    if not topic:
        return []
    segments=[s.strip() for s in re.split(r"(?<=[。！？!?])|\n",str(corpus or "")) if s.strip()]
    # Prefer an exact assertion about the subject, then full topical mentions.
    hits=[s for s in segments if topic in s and len(s)>=7]
    hits.sort(key=lambda s:(not s.startswith(topic+"は"),not s.startswith(topic+"とは"),len(s)))
    return hits[:max_items]

def augment_explicit_answer(topic, existing_answer, corpus, question=None):
    selection=select_evidence(topic,corpus,question)
    classified=selection['selected']
    hits=[item["text"] for item in classified]
    if not hits:
        return {"route":"EXPLICIT_TOPIC_WIKIPEDIA_ONLY","answer":existing_answer,"evidence":[]}
    notes=" / ".join("["+item["role"]+"] "+item["text"] for item in classified)
    if selection["intent"]=="DEFINITION" and not selection["has_direct_definition"]:
        notes = "直接的な定義は見つからず、関連記述を示す。 " + notes
    return {"route":"EXPLICIT_TOPIC_CORPUS_WIKIPEDIA",
            "answer":f"【長門コーパスの関連記述・未検証】{notes}\n【Wikipediaによる説明・外部情報・未検証】{existing_answer}",
            "evidence":hits, "evidence_roles":classified, "question_intent":selection["intent"], "truth_state":"UNVERIFIED",
            "auto_promote":False,"train_ready":False}

def augment_from_file(topic,existing_answer,path="data/data-nagato.txt",question=None):
    source=Path(path)
    if not source.is_file():
        return {"route":"EXPLICIT_TOPIC_WIKIPEDIA_ONLY","answer":existing_answer,"evidence":[]}
    return augment_explicit_answer(topic,existing_answer,source.read_text(encoding="utf-8-sig"),question=question)
