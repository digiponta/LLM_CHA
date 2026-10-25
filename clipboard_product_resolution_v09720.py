"""Resolve product aliases strictly against clipboard-listed products."""
import re
from clipboard_grounded_qa_v0977 import section_items

ALIASES={"黒耳":("黒耳 ver.",),"白耳":("白耳 ver.",)}
REPORT=re.compile(r"(飲んだ(?:ことがある|ことある|ことがあった)?|食べた|試した|買った|飲んでみた)")
TASTE=re.compile(r"(甘かった|酸味|甘さ|苦味|美味しかった|おいしかった|チョコレート)")
QUESTION=re.compile(r"(ですか|ますか|教えて|種類|一覧|検索|どれ|何が|ググって|ぐぐって)")

def resolve(text, utterance):
    products=list(dict.fromkeys(x for section in section_items(text).values() for x in section))
    matches=[p for p in products if p in utterance]
    if not matches:
        for alias,phrases in ALIASES.items():
            if alias in utterance:
                matches.extend(p for p in products if any(phrase in p for phrase in phrases))
    matches=list(dict.fromkeys(matches))
    if len(matches)==1:return {"status":"EXACT","product":matches[0]}
    if len(matches)>1:return {"status":"AMBIGUOUS","products":matches}
    return {"status":"NONE"}

def classify(text,utterance):
    if QUESTION.search(utterance):return None
    intent="EXPERIENCE" if REPORT.search(utterance) else ("TASTE" if TASTE.search(utterance) else None)
    if not intent:return None
    entity=resolve(text,utterance)
    return {"intent":intent,**entity}
