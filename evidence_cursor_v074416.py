"""v0.7.44.16 — provenance-preserving evidence cursor.

Cursor is scoped to one topic and one conversation session. It never modifies
truth labels or the underlying evidence records.
"""
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Evidence:
    proposition_id: str
    subject: str
    text: str
    provenance: str
    truth_state: str = "UNVERIFIED"

@dataclass
class EvidenceCursor:
    subject: str = ""
    records: list[Evidence] = field(default_factory=list)
    presented: set[str] = field(default_factory=set)

    def reset(self, subject: str, records: list[Evidence], initial_text: str = ""):
        self.subject = subject
        self.records = [
            r for r in records
            if r.subject == subject and r.proposition_id and r.text.strip()
            and r.provenance and r.truth_state == "UNVERIFIED"
        ]
        self.presented = {
            r.proposition_id for r in self.records
            if initial_text and r.text.strip() in initial_text
        }

    def next_evidence(self, subject: str):
        if subject != self.subject:
            return None
        for record in self.records:
            if record.proposition_id not in self.presented:
                self.presented.add(record.proposition_id)
                return record
        return None

    def remaining(self):
        return sum(r.proposition_id not in self.presented for r in self.records)

def render_unverified(record: Evidence):
    return (
        f"【原文中の関連記述・未検証】{record.text}\n"
        f"出典：{record.provenance}\n"
        f"（Proposition ID: {record.proposition_id}）"
    )
