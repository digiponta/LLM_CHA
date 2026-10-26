"""Conservative opinion statement detection for Nagato persona v0.9.7.54.

This is an acknowledgement, not factual agreement or verification.
"""
from dataclasses import dataclass
import re

# Only clearly evaluative declarative statements; do not absorb questions
# or unsupported factual propositions.
VALUE_WORDS=("大切","重要","必要","不要","無駄","素晴らしい","難しい")
PAT=re.compile(r"^(?P<topic>[^。！？?「」『』、\n]{1,45}?)(?:は|が)(?P<value>"+
               "|".join(map(re.escape,sorted(VALUE_WORDS,key=len,reverse=True)))+
               r")(?P<negative>ではない|じゃない)?(?:だ|です)?[。！! ]*$")

@dataclass(frozen=True)
class Opinion:
    topic:str
    predicate:str
    negated:bool
    response:str="そう。"
    intent:str="OPINION"
    truth_state:str="USER_OPINION_UNVERIFIED"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False

def detect(text):
    s=str(text or "").strip()
    if not s or "とは" in s or any(x in s for x in ("？","?","とは何","教えて","どうして")):
        return None
    m=PAT.fullmatch(s)
    if not m:return None
    topic=m.group("topic").strip()
    if not topic or "けど" in topic or "けれど" in topic:return None
    return Opinion(topic,m.group("value"),bool(m.group("negative")))
