"""Read-only role classification for Nagato corpus excerpts.

Classifies textual role, *not* physical or factual correctness.
"""
import re

ROLE_PRIORITY={"DIRECT_DEFINITION":0,"SUBJECT_RELATION":1,"TOPIC_DISCUSSION":2,"INCIDENTAL_MENTION":3}

def classify(topic, sentence):
    topic=str(topic or "").strip()
    sentence=str(sentence or "").strip()
    if not topic or topic not in sentence:
        return None
    # Respect the grammatical subject. '数学は文学の分類' is about 数学,
    # not a definition of 文学.
    if re.match(r"^"+re.escape(topic)+r"(?:とは|というのは)",sentence):
        return "DIRECT_DEFINITION"
    if re.match(r"^"+re.escape(topic)+r"は[、\s]*",sentence):
        if re.search(r"(?:である|を指す|のことである|と定義される)(?:。|$)",sentence):
            return "DIRECT_DEFINITION"
        return "SUBJECT_RELATION"
    if len(sentence)<22 or re.search(r"(?:に通じる言葉|のアナロジ)[。！]?$",sentence):
        return "INCIDENTAL_MENTION"
    if re.match(r"^.{1,20}は[、\s]*",sentence) and topic not in sentence[:len(topic)+2]:
        # Explicitly different subject: a relation whose object mentions topic.
        return "INCIDENTAL_MENTION"
    return "TOPIC_DISCUSSION"

def rank_mentions(topic, corpus, max_items=2):
    segments=[s.strip() for s in re.split(r"(?<=[。！？!?])|\n",str(corpus or "")) if s.strip()]
    entries=[]
    for i,s in enumerate(segments):
        role=classify(topic,s)
        if role is not None:
            entries.append({"text":s,"role":role,"position":i})
    entries.sort(key=lambda x:(ROLE_PRIORITY[x["role"]],x["position"]))
    return entries[:max_items]
