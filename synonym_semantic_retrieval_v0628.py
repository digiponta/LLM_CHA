"""v0.6.28 synonym-aware resolution trace and semantic relation boundaries.

Only approved lexical equivalence edges permit query rewriting. RELATED and
BROADER/NARROWER must never be substituted as synonyms.
"""
from dataclasses import dataclass, asdict
import json

@dataclass(frozen=True)
class RetrievalTrace:
    requested: str
    matched: str
    relation: str
    channel: str
    source: str
    truth_state: str
    def as_json(self):
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

RELATIONS={"SYNONYM","RELATED","BROADER","NARROWER"}

def equivalent_terms(lexicon,term):
    return lexicon.expand(term)

def allowable_substitution(relation):
    if relation not in RELATIONS:
        raise ValueError("unknown semantic relation")
    return relation=="SYNONYM"

def trace_match(requested,matched,channel,source,truth_state):
    return RetrievalTrace(requested=requested,matched=matched,
        relation="EXACT" if requested==matched else "SYNONYM",
        channel=channel,source=source,truth_state=truth_state)
