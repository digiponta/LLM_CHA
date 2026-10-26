"""Compare independently-maintained live journal focus with Event Replay.

Only compare properties the live runtime actually maintains. Never use replay
as the 'actual' state; that would make the check tautological.
"""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class ConsistencyResult:
    status: str
    mismatches: tuple
    replay_complete: bool
    replay_sequence: int
    def to_dict(self):
        d=asdict(self)
        d["mismatches"]=list(self.mismatches)
        return d

def validate_semantic_consistency(journal, runtime_active_topic=None):
    replay=journal.replay()
    if not replay.complete:
        return ConsistencyResult("INCOMPLETE",(),False,replay.last_sequence)
    mismatch=[]
    replay_focus={topic: entry["quality"] for topic,entry in replay.preferences.items()
                  if entry.get("quality") is not None}
    live_focus=dict(journal.focus)
    if replay_focus != live_focus:
        mismatch.append("quality_focus")
    if runtime_active_topic is not None and replay.active_topic != runtime_active_topic:
        mismatch.append("active_topic")
    return ConsistencyResult("MISMATCH" if mismatch else "CONSISTENT",
                             tuple(mismatch),True,replay.last_sequence)
