"""Evidence-first routing of named-topic prompts without declaring KNOWN = ANSWERABLE."""
import re

_TOPIC = re.compile(r"^(.{2,40}?)(?:の話題|について話して|について話そう)[。！!？?\s]*$")

def topic_for_external_evidence(utterance):
    value=utterance.strip()
    if not value or value.startswith("/"): return None
    match=_TOP.fullmatch(value)
    if not match: return None
    subject=match.group(1).strip()
    if len(subject)<2 or subject in {"私","あなた","貴方","長門","こんにちは","ありがとう"}:
        return None
    return subject

def source_is_usable(result):
    return (isinstance(result,dict) and result.get("status")=="FOUND"
            and isinstance(result.get("answer"),str)
            and len(result["answer"].strip())>=15
            and bool(result.get("source")))
