"""Temporary source-text retriever. It never promotes evidence to verified memory."""
import re
from dataclasses import dataclass

STOP=frozenset(("です","ます","とは","について","教えて","ください","どんな","どうして","なぜ","その","この","それ","あります","知りたい","何ですか","何","もの","こと","特徴"))
QUESTION_MARKERS=("とは","何","どんな","どこ","いつ","なぜ","どう","成分","組成","特徴","含む","材料","原料","屈折率","カット","研磨","メニュー","フード","ドリンク","種類","について","教えて","知りたい","？","?")
@dataclass(frozen=True)
class EvidenceHit:
    text: str
    score: int

def evidence_question(text):
    return any(marker in text for marker in QUESTION_MARKERS)

def tokens(text):
    words=re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[一-龯々ァ-ヴー]{2,}",text.casefold())
    words=[piece for word in words for piece in re.split(r"(?:について|教えて|ください|知りたい|とは|ですか|の|は|が|を|に|で|と)",word) if len(piece)>=2]
    found=[]
    for word in words:
        if word not in STOP and word not in found:
            found.append(word)
    return found

def fragments(source, max_length=320):
    result=[]
    # Preserve nearby meaning; do not join unrelated lines or fabricate facts.
    for part in re.split(r"(?<=[。！？!?])\s*|[\r\n]+",source):
        part=" ".join(part.split())
        while len(part)>max_length:
            result.append(part[:max_length])
            part=part[max_length:]
        if part:
            result.append(part)
    return result

def retrieve(source, question, *, limit=3):
    """Return exact source excerpts, or an empty list for insufficient support."""
    if not source.strip() or not evidence_question(question):
        return []
    terms=tokens(question)
    if not terms:
        return []
    hits=[]
    for part in fragments(source):
        folded=part.casefold()
        matching=[term for term in terms if term in folded]
        if not matching:
            continue
        # Reject generic common prefixes as unsupported relevance.
        score=sum(min(len(term),12) for term in matching)
        hits.append(EvidenceHit(part,score))
    hits.sort(key=lambda h:-h.score)
    return hits[:limit]

def answer_from_evidence(source,question):
    hits=retrieve(source,question)
    if not hits:
        return None
    return "資料の該当箇所（クリップボード由来・未検証）: "+" / ".join(h.text for h in hits)
