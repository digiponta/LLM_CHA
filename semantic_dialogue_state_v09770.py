"""Ephemeral semantic dialogue frames for user-reported preferences.

Frames describe speech acts, never assert external factual truth.
"""
from dataclasses import dataclass, asdict
import re
from topic_preference_ack_v09767 import PREFERENCE

@dataclass(frozen=True)
class DialogueFrame:
    topic: str
    intent: str
    attribute: str | None
    quality: str | None
    emotion: str | None
    speaker: str = "user"
    truth_state: str = "USER_REPORTED"

    def to_dict(self):
        return asdict(self)

def extract_preference(text):
    m=PREFERENCE.fullmatch(str(text or "").strip())
    if not m:
        return None
    subject=m.group("subject").strip("、, ")
    if not subject:
        return None
    return DialogueFrame(subject, "express_preference", None, None, "likes")

def extract_reason(text, topic):
    if not topic:
        return None
    utterance=str(text or "").strip().rstrip("。！？!? ")
    quality = None
    for pattern,value in (
        (r"きらきら|キラキラ|輝", "sparkling"),
        (r"虹色|ファイア", "colorful_fire"),
        (r"きれい|綺麗|美しい", "beautiful"),
    ):
        if re.search(pattern,utterance):
            quality=value
            break
    if not quality:
        return None
    if not re.search(r"ところ|感じ|から|心地よい|好き|素敵|きれい|綺麗|美しい",utterance):
        return None
    emotion = "comfort" if "心地よい" in utterance else "likes" if "好き" in utterance else "positive"
    return DialogueFrame(topic,"explain_preference","appearance",quality,emotion)
