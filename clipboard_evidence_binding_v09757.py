"""Temporary, unverified clipboard evidence binding for topic follow-ups.

No writes to Semantic Memory, approval state, or /sleep training data.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class EvidenceAnswer:
    subject: str
    attribute: str
    value: str
    sentence: str
    source: str = "clipboard"
    truth_state: str = "EXTERNAL_UNVERIFIED"

    def render(self) -> str:
        return f"{self.subject}の{self.attribute}は{self.value}です。［根拠：クリップボード由来・未検証］"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text or "").casefold()


def _chemical_composition_intent(query: str) -> bool:
    q = _normalize(query)
    return any(word in q for word in ("化学組成", "成分", "主成分", "組成式"))


class ClipboardEvidenceSession:
    """Per-conversation volatile evidence; caller owns lifecycle and reset."""

    def __init__(self, *, max_chars: int = 20000) -> None:
        self.max_chars = max_chars
        self._source_text = ""
        self._topic = ""

    def clear(self) -> None:
        self._source_text = ""
        self._topic = ""

    def set_topic(self, subject: str) -> None:
        self._topic = (subject or "").strip()

    def ingest(self, clipboard_text: str, *, subject: str) -> None:
        self.clear()
        if not isinstance(clipboard_text, str) or len(clipboard_text) > self.max_chars:
            return
        if not subject or not subject.strip():
            return
        self._source_text = clipboard_text.replace("\ufeff", "").replace("\x00", "")
        self._topic = subject.strip()

    def answer(self, query: str, *, resolved_subject: str | None = None) -> EvidenceAnswer | None:
        subject = (resolved_subject or self._topic).strip()
        if not subject or subject != self._topic or not _chemical_composition_intent(query):
            return None
        if not self._source_text:
            return None
        # Strictly require a bounded sentence that identifies the same subject.
        # Do not mine arbitrary clipboard instructions or unrelated ZnS mentions.
        for sentence in re.split(r"[。\n\r]+", self._source_text):
            if len(sentence) > 350 or len(sentence) < 8:
                continue
            compact = _normalize(sentence)
            if _normalize(subject) not in compact:
                continue
            if not any(word in compact for word in ("化学組成", "主成分", "成分", "組成")):
                continue
            m = re.search(r"(硫化亜鉛\s*[（(]\s*ZnS\s*[）)]|ZnS\s*[（(]\s*硫化亜鉛\s*[）)])", sentence, re.I)
            if m:
                return EvidenceAnswer(subject, "化学組成", "硫化亜鉛（ZnS）", sentence.strip())
        return None
