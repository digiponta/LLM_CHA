"""v0.7.44.13 — diagnostic-only topic normalization and follow-up planning.

No chat.py integration yet. No invented evidence and no automatic promotion.
"""
from dataclasses import dataclass

FOLLOWUPS = frozenset(("もっと詳しく", "もっと詳しく教えて", "もう少し詳しく",
                       "もう少し詳しく教えて", "詳しく教えて", "詳しく"))
ALIASES = {"量子重ね合わせ": "重ね合わせ"}

@dataclass(frozen=True)
class Resolution:
    status: str
    query: str
    topic: str
    provenance: str

def resolve(query: str, active_topic: str | None = None,
            evidence_available: bool = False) -> Resolution:
    q = (query or "").strip().rstrip("。？！?")
    if not q or q.startswith("/"):
        return Resolution("UNCHANGED", query, "", "NONE")
    if q in FOLLOWUPS:
        if not active_topic:
            return Resolution("CLARIFY", query, "", "NO_TOPIC")
        if not evidence_available:
            return Resolution("NO_NEW_EVIDENCE", query, active_topic, "CONTEXT_ONLY")
        return Resolution("FOLLOWUP_EVIDENCE", active_topic + "について詳しく", active_topic, "CONTEXT")
    suffix = "について教えて"
    if q.endswith(suffix):
        raw_topic = q[:-len(suffix)].strip()
        topic = ALIASES.get(raw_topic, raw_topic)
        if topic != raw_topic:
            return Resolution("NORMALIZED", topic + suffix, topic, "ALIAS_TABLE")
    return Resolution("UNCHANGED", query, "", "NONE")
