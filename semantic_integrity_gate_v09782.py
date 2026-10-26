"""Fail-closed gate for dialogue-state-derived answers, not ordinary evidence retrieval."""
from dataclasses import dataclass, asdict
from cross_context_consistency_v09779 import validate_cross_context
from semantic_topic_isolation_v09781 import validate_topic_isolation

@dataclass(frozen=True)
class GateDecision:
    status: str
    allow_dialogue: bool
    reasons: tuple
    def to_dict(self):
        x=asdict(self);x["reasons"]=list(self.reasons);return x

def evaluate_integrity(manager, topic_context=None):
    isolation=validate_topic_isolation(manager.journal)
    cross=validate_cross_context(manager,topic_context)
    reasons=[]
    if isolation.status!="ISOLATED":reasons.append("isolation:"+isolation.status)
    if cross.status in ("MISMATCH","INCOMPLETE"):reasons.append("consistency:"+cross.status)
    if reasons:return GateDecision("BLOCK",False,tuple(reasons))
    if cross.status=="NOT_COMPARABLE":
        return GateDecision("PARTIAL",True,("topic_context_not_comparable",))
    return GateDecision("ALLOW",True,())
