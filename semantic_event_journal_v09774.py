"""Session-only audit of semantic dialogue transitions. No disk writes."""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class SemanticEvent:
    sequence: int
    event: str
    topic: str | None
    previous_quality: str | None = None
    updated_quality: str | None = None
    truth_state: str = "USER_REPORTED"
    persistence: str = "SESSION_ONLY"

    def to_dict(self):
        return asdict(self)

class SemanticEventJournal:
    def __init__(self, max_events=64):
        self.max_events=max_events
        self.events=[]
        self.sequence=0
        self.focus={}
    def record(self,event,topic,previous_quality=None,updated_quality=None):
        self.sequence+=1
        item=SemanticEvent(self.sequence,event,topic,previous_quality,updated_quality)
        self.events.append(item)
        if len(self.events)>self.max_events:
            self.events.pop(0)
        if event in ("correct_preference", "clarification_provided") and topic and updated_quality:
            self.focus[topic]=updated_quality
        elif event=="explain_preference" and topic and updated_quality:
            self.focus[topic]=updated_quality
        elif event=="reject_previous" and topic:
            self.focus.pop(topic,None)
        return item
    def latest(self):
        return self.events[-1] if self.events else None
