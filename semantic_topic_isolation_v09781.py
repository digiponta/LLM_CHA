"""Session-only topic provenance and attribute-isolation audit.

Audit journal events independently of Replay; incomplete journals are not certifiable.
"""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class IsolationResult:
    status: str
    violations: tuple
    checked_events: int
    def to_dict(self):
        d=asdict(self)
        d["violations"]=list(self.violations)
        return d

def validate_topic_isolation(journal):
    events=journal.events
    replay=journal.replay()
    if not replay.complete:
        return IsolationResult("INCOMPLETE",(),len(events))
    violations=[]
    current=None
    per_topic={}
    for e in events:
        if e.truth_state!="USER_REPORTED" or e.persistence!="SESSION_ONLY":
            violations.append(f"{e.sequence}:trust_boundary")
            continue
        if e.event=="switch_topic":
            if e.topic!=e.target_topic or not e.target_topic:
                violations.append(f"{e.sequence}:invalid_destination")
            if not e.source_topic:
                violations.append(f"{e.sequence}:missing_source")
            if current is not None and e.source_topic!=current:
                violations.append(f"{e.sequence}:broken_continuity")
            if e.previous_quality is not None or e.updated_quality is not None:
                violations.append(f"{e.sequence}:quality_on_switch")
            current=e.target_topic
        elif e.event in ("express_preference","explain_preference","correct_preference",
                         "reject_previous","clarification_acknowledged","clarification_provided",
                         "clarification_cancelled","agreement"):
            if e.source_topic is not None or e.target_topic is not None:
                violations.append(f"{e.sequence}:unexpected_transfer")
            if not e.topic:
                violations.append(f"{e.sequence}:missing_topic")
                continue
            if current is not None and e.topic!=current:
                violations.append(f"{e.sequence}:cross_topic_write")
            current=e.topic
            if e.event in ("explain_preference","correct_preference","clarification_provided") and e.updated_quality:
                per_topic[e.topic]=e.updated_quality
            if e.event=="reject_previous":
                per_topic.pop(e.topic,None)
    if per_topic != dict(journal.focus):
        violations.append("quality_focus_mismatch")
    return IsolationResult("VIOLATION" if violations else "ISOLATED",tuple(violations),len(events))
