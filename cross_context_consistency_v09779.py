"""Cross-context consistency; only compare observed, comparable fields."""
from dataclasses import dataclass,asdict
from semantic_state_consistency_v09778 import validate_semantic_consistency

@dataclass(frozen=True)
class CrossContextResult:
    status: str
    mismatches: tuple
    compared: tuple
    not_comparable: tuple
    replay_sequence: int
    def to_dict(self):
        d=asdict(self)
        for key in ("mismatches","compared","not_comparable"):
            d[key]=list(d[key])
        return d

def validate_cross_context(manager, topic_context=None, semantic_memory=None):
    replay=manager.journal.replay()
    base=validate_semantic_consistency(manager.journal)
    unavailable=("semantic_memory",)  # User-reported transient state != learned facts.
    if not replay.complete:
        return CrossContextResult("INCOMPLETE",(),("quality_focus",),unavailable,replay.last_sequence)
    issues=list(base.mismatches)
    compared=["quality_focus"]
    # TopicContext may be a previous Google-search topic, rather than dialogue
    # topic. Only compare if it was explicitly switched by the dialogue manager.
    topic_switch=any(e.event=="switch_topic" for e in manager.journal.events)
    if topic_switch and topic_context is not None:
        compared.append("topic_context.active_topic")
        if getattr(topic_context,"active_topic",None)!=replay.active_topic:
            issues.append("topic_context.active_topic")
    else:
        unavailable+=("topic_context.active_topic",)
    compared.extend(("manager.awaiting_clarification", "manager.awaiting_new_reason"))
    if replay.awaiting_clarification != manager.awaiting_clarification:
        issues.append("manager.awaiting_clarification")
    if replay.awaiting_new_reason != manager.awaiting_new_reason:
        issues.append("manager.awaiting_new_reason")
    return CrossContextResult("MISMATCH" if issues else ("CONSISTENT" if len(compared)>1 else "NOT_COMPARABLE"),
        tuple(issues),tuple(compared),unavailable,replay.last_sequence)
