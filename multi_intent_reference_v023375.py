"""v0.2.33.75: conservative multi-intent preprocessing and ambiguous reference prompt.

Only explicit standalone greeting prefix + clearly phrased concept question is
rewritten to an existing 'Xとは' query (thus reusing its Truth-Aware gate).
No automatic reference approval or truth promotion.
"""
import re

GREETING=r"(?:こんにちは|こんばんは|おはようございます|おはよう|やあ)"
CONCEPT=r"[\w一-龥ぁ-んァ-ヶー]{1,32}"
AMBIGUOUS=frozenset(("昨日の続き","昨日の実験の続き","あの実験","この前の続き","前回の続き"))

def split_input(text):
    raw=(text or "").strip()
    if raw.startswith("/"):return raw,None
    if re.fullmatch(r"(?:昨日の続き|昨日の実験の続き|あの実験|この前の続き|前回の続き)[。！？!?]?",raw):
        return raw,"REFERENCE_CLARIFY"
    match=re.fullmatch(rf"({GREETING})[、,，]\s*({CONCEPT})(?:について教えて|とは[何なに]?)(?:ください|下さい)?[。！？!?]?",raw)
    if match:
        subject=match.group(2)
        return subject+"とは","GREETING_PLUS_KNOWLEDGE"
    return raw,None

def clarify_reference():
    return "どの実験・話題の続きでしょうか？対象を具体的に教えてください。"
