"""Temporary, unverified evidence topic for contextual follow-up questions.

No knowledge promotion, no inference of comparative facts, and no response to
unrelated user remarks. The caller owns the clipboard source lifecycle.
"""
import re
from dataclasses import dataclass
from temporary_evidence_retriever_v0137 import fragments

ATTRS={
    "化学組成":("化学組成","組成","成分"),
    "屈折率":("屈折率",),
    "カット":("カット","研磨","加工"),
}
COMPARISON=("高いの","高いですか","低いの","低いですか","普通なの","他と比べ","どのくらい高い")

@dataclass
class EvidenceTopic:
    subject: str=""
    attribute: str=""
    source_id: str=""
    excerpt: str=""

class EvidenceTopicContext:
    def __init__(self):
        self.state=EvidenceTopic()

    def reset(self):
        self.state=EvidenceTopic()

    def answer(self, source, utterance):
        text=utterance.strip().rstrip("。！？!? ")
        if not source.strip():
            self.reset()
            return None
        if self.state.source_id and self.state.source_id!=source:
            self.reset()
        prior=self.state
        # Comparison references only the immediately retained evidence.
        if text in ("それは高いの","それは高いのですか","それは高いですか","それは低いの","それは普通なの"):
            if not (prior.subject and prior.attribute and prior.excerpt):
                return None
            return f"{prior.subject}の{prior.attribute}についてですね。資料には「{prior.excerpt}」とありますが、比較基準が確認できないため、高低は判断できません。（未検証）"
        attribute=next((key for key,aliases in ATTRS.items() if any(a in text for a in aliases)),None)
        if not attribute:
            return None
        # Extract an explicit subject or restore it from the previous question.
        subject=""
        explicit=re.match(r"^(.{2,50}?)の(?:化学組成|組成|成分|屈折率|カット|研磨|加工)",text)
        if explicit:
            subject=explicit.group(1).strip()
        elif prior.subject:
            subject=prior.subject
        if not subject:
            return None
        # The subject AND selected attribute must co-occur in a source excerpt;
        # no unrelated span may be used as backing evidence.
        aliases=ATTRS[attribute]
        hits=[part for part in fragments(source) if subject.casefold() in part.casefold()
              and any(alias in part for alias in aliases)]
        if not hits:
            self.state=EvidenceTopic(subject,attribute,source,"")
            return f"{subject}の{attribute}について、取り込んだ資料から直接の記述を確認できませんでした。（未検証）"
        excerpt=hits[0]
        self.state=EvidenceTopic(subject,attribute,source,excerpt)
        return f"{subject}の{attribute}について、資料の該当箇所（未検証）: {excerpt}"
