"""Read-only personal-preference intent guard v0.9.7.50."""
from dataclasses import dataclass,asdict
import re

PATTERN=re.compile(r"^(?:(?:私は|僕は|わたしは)\s*)?(?P<object>[^。！？?「」\n]{1,100}?)(?P<also>も)?(?P<polarity>大好き|好き|嫌い|苦手)(?:だ|です|なの|なんだ)?[。！! ]*$")
NEGATIVE={"嫌い","苦手"}
@dataclass(frozen=True)
class Preference:
    subject:str
    predicate:str
    object:str
    polarity:str
    response:str
    source:str="USER_UTTERANCE"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def detect(text):
    t=str(text or "").strip()
    if not t or any(x in t for x in ("？","?","とは","について教えて","好きですか","好き？")):return None
    m=PATTERN.fullmatch(t)
    if m is None:return None
    obj=m.group("object").strip(" 、")
    if not obj or "、" in obj or "けど" in obj or "けれど" in obj:return None
    from semantic_context_surface_v09755 import repair_preference_object
    obj=repair_preference_object(obj)
    if not obj:return None
    p=m.group("polarity")
    if p in NEGATIVE:
        reply=obj+"は"+("苦手" if p=="苦手" else "好きではない")+"んだね。"
    else:
        reply=obj+"も好きなんだね。" if m.group("also") else obj+"が好きなんだね。"
    return Preference("USER","LIKE" if p not in NEGATIVE else "DISLIKE",
                      obj,"NEGATIVE" if p in NEGATIVE else "POSITIVE",reply)
