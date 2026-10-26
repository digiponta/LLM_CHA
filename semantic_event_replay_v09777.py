"""Replay bounded, session-only Semantic Dialogue events into current state.

Full reconstruction requires an untruncated journal; report incomplete otherwise.
"""
from dataclasses import dataclass, field, asdict

@dataclass
class ReplayState:
    active_topic: str | None = None
    preferences: dict = field(default_factory=dict)
    rejected_qualities: dict = field(default_factory=dict)
    truth_state: str = "USER_REPORTED"
    complete: bool = True
    last_sequence: int = 0

    def to_dict(self):
        return asdict(self)

def replay_semantic_events(events):
    state=ReplayState()
    if not events:
        return state
    if events[0].sequence != 1:
        state.complete=False
    expected=events[0].sequence
    for e in events:
        if e.sequence != expected:
            state.complete=False
        expected=e.sequence+1
        state.last_sequence=e.sequence
        if e.truth_state != "USER_REPORTED" or e.persistence != "SESSION_ONLY":
            state.complete=False
            continue
        topic=e.topic
        if e.event=="switch_topic":
            state.active_topic=topic
            continue
        if topic is None:
            continue
        if e.event=="express_preference":
            state.active_topic=topic
            state.preferences.setdefault(topic,{"preference":"likes","quality":None})
        elif e.event in ("explain_preference","correct_preference","clarification_provided"):
            state.active_topic=topic
            entry=state.preferences.setdefault(topic,{"preference":"likes","quality":None})
            if e.event=="correct_preference" and e.previous_quality:
                rejected=state.rejected_qualities.setdefault(topic,[])
                if e.previous_quality not in rejected:
                    rejected.append(e.previous_quality)
            if e.updated_quality:
                entry["quality"]=e.updated_quality
        elif e.event=="reject_previous":
            state.active_topic=topic
            entry=state.preferences.setdefault(topic,{"preference":"likes","quality":None})
            previous=e.previous_quality or entry["quality"]
            if previous:
                rejected=state.rejected_qualities.setdefault(topic,[])
                if previous not in rejected:
                    rejected.append(previous)
            entry["quality"]=None
    return state
