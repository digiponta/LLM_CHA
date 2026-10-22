"""v0.6.16 priority policy for raw non-subject retrieval."""
import re

def conversational_intercept(text):
    """Return a safe clarification for incomplete second-person questions."""
    value=text.strip()
    if re.fullmatch(r"(貴方|あなた|君|きみ)(?:は|って|とは)?[？?]?", value):
        return "私について、何を知りたい？ 名前や好きなことなら答えられる。"
    return None

def allow_raw_evidence(text, focus):
    """Personas, conversational intents and questions bypass lexical evidence."""
    t=text.strip()
    f=(focus or "").strip()
    if not t or t.startswith("/"):
        return False
    if f in {"長門","長門有希","あなた","貴方","私","君","きみ"}:
        return False
    if t in {"こんにちは","こんばんは","おはよう","ありがとう","さようなら"}:
        return False
    # Only short, concept-focused queries: not arbitrary multi-clause questions.
    return t in {f,f+"は",f+"とは",f+"について",f+"って"} or t in {f+"？", f+"?"}
