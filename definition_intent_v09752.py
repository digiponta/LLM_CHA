"""Definition intent and relevance guard v0.9.7.52.

Conservative: known dictionary-style concepts get a curated local
definition; unsupported concepts are handed to the existing search
pipeline without treating disambiguation as a verified definition.
"""
from dataclasses import dataclass,asdict
import re

DEFINITIONS={
 "満足":"満足とは、期待や欲求が満たされ、十分だと感じる状態のことです。",
}
DISAMBIGUATION_MARKERS=("曖昧さ回避","この項目では","以下のいずれか","同名の","K.349","K.473")
@dataclass(frozen=True)
class DefinitionIntent:
    target:str
    intent:str
    response:str|None
    route:str
    truth_state:str
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def resolve(text):
    s=str(text or "").strip()
    if "とは" not in s or s.startswith("/"):return None
    # The literal 「とは」 is a search-intent trigger. This narrow
    # direct-definition route handles only exact simple forms.
    m=re.fullmatch(r"(?P<term>[^「」『』。！？?\n]{1,60}?)とは(?:何(?:ですか|か)|どういう意味(?:ですか|か))?[。？? ]*",s)
    if m is None:
        return DefinitionIntent("", "DEFINITION_SEARCH", None,
                                "EXISTING_SEARCH","UNVERIFIED")
    term=m.group("term").strip()
    if term in DEFINITIONS:
        return DefinitionIntent(term,"DEFINITION",DEFINITIONS[term],
                                "CURATED_DEFINITION","LOCAL_CURATED")
    return DefinitionIntent(term,"DEFINITION_SEARCH",None,
                            "EXISTING_SEARCH","UNVERIFIED")

def is_relevant_definition(term,article_title,article_text):
    title=str(article_title or "").strip()
    body=str(article_text or "")
    if not title or not body or any(m in title or m in body for m in DISAMBIGUATION_MARKERS):
        return False
    if title!=str(term or "").strip():return False
    return len(body.strip())>=35
