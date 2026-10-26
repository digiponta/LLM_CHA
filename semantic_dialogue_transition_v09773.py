"""Ephemeral dialogue transitions. Explicit corrections only; no inference."""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Transition:
    intent: str
    topic: str | None
    quality: str | None = None

def parse_transition(text, current_topic, previous_frame):
    q=str(text or "").strip().rstrip("。！？!? ")
    if not q or q.startswith("/"):
        return None
    switch=re.fullmatch(r"ところで[、, ]*(.{2,45}?)(?:は|について)(?:どう|？|\?|)$",q)
    if switch:
        return Transition("switch_topic",switch.group(1).strip())
    if previous_frame and previous_frame.intent=="explain_preference":
        if q in ("そうじゃない","違う","そうではない","違います"):
            return Transition("reject_previous",previous_frame.topic)
        correction=re.fullmatch(r"(?:きらきら|キラキラ|輝き)より(?:も)?(?P<new>色|色合い|形|透明感)が好き(?:です)?",q)
        if correction:
            return Transition("correct_preference",previous_frame.topic,correction.group("new"))
    return None
