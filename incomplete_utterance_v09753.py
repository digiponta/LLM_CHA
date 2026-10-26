"""Conservative incomplete-utterance guard for Japanese chat v0.9.7.53.

Avoid treating an unfinished topical phrase as a Wikipedia lookup.
No persistent memory, learned facts, or auto promotion.
"""
from dataclasses import dataclass, asdict
import re

PARTICLES=("は","が","を","に","へ","と","も","で")
EXCLUDED=("とは",)
@dataclass(frozen=True)
class IncompleteUtterance:
    topic:str
    particle:str
    response:str
    route:str="INCOMPLETE_UTTERANCE"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def detect(text):
    s=str(text or "").strip()
    if not s or s.startswith("/") or "とは" in s:
        return None
    if any(x in s for x in ("。","！","!","？","?","、","\n","「","」","『","』")):
        return None
    if s in ("はい","いいえ","そう","でも","それで","そして"):
        return None
    if len(s)>40 or len(s)<2:
        return None
    particle=s[-1]
    if particle not in PARTICLES or any(s.endswith(x) for x in EXCLUDED):
        return None
    topic=s[:-1].strip()
    if not topic or not re.fullmatch(r"[\w&・ー＋+\-％%　 ]+",topic):
        return None
    return IncompleteUtterance(topic,particle,f"{topic}について、何を知りたい？")
