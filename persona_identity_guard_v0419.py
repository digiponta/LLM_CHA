"""v0.4.19 conservative self-identity question route.

Only established Nagato persona identity. Not general factual question routing.
"""
from __future__ import annotations
import re
import unicodedata

IDENTITY="長門有希。"
_PATTERN=re.compile(
    r"^(?:(?:あなた|貴方|君|きみ|お前|あなた自身|貴方自身)(?:は|って|の名前は)?(?:誰|だれ|何者)|"
    r"(?:あなた|貴方|君|きみ)(?:の)?名前(?:は|を教えて)?|"
    r"(?:お名前)(?:は|を教えて)?|"
    r"(?:自己紹介して|自己紹介をして|名前を教えて))(?:ですか|なの|でしょうか)?[?？。!！]*$"
)
# Exclude sentence fragments such as "貴方は", factual third-party names,
# metalinguistic prompts, and substring matches.
def identity_answer(question: str, *, persona_id: str="nagato") -> str | None:
    if persona_id!="nagato" or not isinstance(question,str) or len(question)>80:
        return None
    q=unicodedata.normalize("NFKC",question).strip().replace(" ","").replace("　","")
    if q.startswith("/") or "\n" in q or "\r" in q:
        return None
    return IDENTITY if _PATTERN.fullmatch(q) else None
