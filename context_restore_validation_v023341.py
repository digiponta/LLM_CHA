"""v0.2.34.1: fail-closed validation of a restored context checkpoint.

The caller must supply a fresh authoritative corpus and subject Truth Gate result.
No persisted truth decisions are trusted; all proposition IDs are recomputed.
"""
from __future__ import annotations
from dataclasses import dataclass
from longterm_context_v02340 import ContextCheckpoint
from proposition_truth_v0233827 import TruthOverlay, proposition_id

@dataclass(frozen=True)
class CurrentProposition:
    statement: str
    provenance: str

@dataclass(frozen=True)
class CurrentSubject:
    propositions: tuple[CurrentProposition, ...]
    truth_state: str
    allowed: bool

@dataclass(frozen=True)
class RestoreReport:
    context: ContextCheckpoint
    retained: int
    rejected: int
    invalid_topics: tuple[str, ...]

def validate_restored_context(
    snapshot: str,
    current: dict[str, CurrentSubject],
    overlay: TruthOverlay,
) -> RestoreReport:
    """Re-authorize every saved ID against *current* corpus and truth decisions.

    A mismatched ID, missing subject, changed provenance or currently blocked
    proposition is dropped. No generated text or automatic review takes place.
    Duplicate authoritative corpus IDs fail closed by rejecting that ID.
    """
    old = ContextCheckpoint.restore(snapshot)
    result = ContextCheckpoint()
    retained = rejected = 0
    invalid_topics = []
    for topic, old_ids in old.topics.items():
        subject = current.get(topic)
        if not isinstance(subject, CurrentSubject):
            invalid_topics.append(topic)
            rejected += len(old_ids)
            continue
        authorized: set[str] = set()
        duplicates: set[str] = set()
        for prop in subject.propositions:
            if not isinstance(prop, CurrentProposition):
                raise ValueError("invalid current corpus record")
            pid = proposition_id(topic, prop.statement, prop.provenance)
            if pid in authorized:
                duplicates.add(pid)
                continue
            decision = overlay.decide(
                topic, prop.statement, prop.provenance,
                subject.truth_state, subject.allowed
            )
            if decision.allowed:
                authorized.add(pid)
        authorized.difference_update(duplicates)
        accepted = [pid for pid in old_ids if pid in authorized]
        rejected += len(old_ids) - len(accepted)
        retained += len(accepted)
        if accepted:
            for pid in accepted:
                result.remember(topic, pid)
        else:
            invalid_topics.append(topic)
    if old.active_topic in result.topics:
        result.switch(old.active_topic)
    else:
        result.active_topic = None
    return RestoreReport(result, retained, rejected, tuple(invalid_topics))
