"""Conservative, extractive causal evidence search for Japanese short questions."""
import re

CAUSE_QUESTION = re.compile(r"なぜ|どうして|理由|なんで")
CAUSE_MARKER = re.compile(r"ため|ので|ことから|によって|ゆえに|ことが理由|ために")
CUT_TARGET = re.compile(r"カット|研磨|加工|ファセット")
HARDNESS = re.compile(r"硬度.{0,25}(?:低|3[.．]5|4)|(?:低い|低く).{0,18}硬度")
CLEAVAGE = re.compile(r"劈開|割れやす|脆い|もろい")
CUT_DIFFICULTY = re.compile(r"カット.{0,16}(?:難し|困難)|(?:カット|加工|研磨)しにく|難し.{0,12}カット")

def is_causal_question(question):
    return bool(CAUSE_QUESTION.search(question or ""))

def retrieve_cause(store, question):
    if not is_causal_question(question):
        return None
    if not store.topic:
        return {"status":"NO_TOPIC"}
    if not store.records:
        return {"status":"NO_EVIDENCE","topic":store.topic}
    records=[r for r in reversed(store.records) if r["topic"]==store.topic]
    if not records:
        return {"status":"NO_EVIDENCE","topic":store.topic}
    if not CUT_TARGET.search(question):
        return {"status":"UNSUPPORTED_CAUSE","topic":store.topic}
    for record in records:
        text=record["text"]
        if store.topic.lower() not in text.lower():
            continue
        lines=[line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            # Only a single explicit sentence containing cause, consequence and linkage.
            if len(line)>350 or len(line)<15:
                continue
            if not (CUT_DIFFICULTY.search(line) and CAUSE_MARKER.search(line)):
                continue
            if not (HARDNESS.search(line) or CLEAVAGE.search(line)):
                continue
            return {"status":"SUPPORTED_EXCERPT","topic":store.topic,
                    "source":record["source"],
                    "source_title":record.get("source_title",record["source"]),
                    "source_url":record.get("source_url",""),
                    "quote":line,"truth_state":"EXTERNAL_UNVERIFIED"}
    return {"status":"NO_CAUSAL_EVIDENCE","topic":store.topic}
