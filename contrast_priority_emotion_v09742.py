"""Contrast-priority semantic operator, isolated experimental v0.9.7.42.

Preserve all emotion components. A late explicit emotion after けれど
is primary; its axis becomes weakly signed neutral (+/- 0.25).
This is a semantic convention, not a psychological measurement.
"""
from dataclasses import dataclass,asdict
import re
from multi_axis_emotion_v09741 import detect_multi

CONNECTOR=re.compile(r"けれども|けれど|だけど|しかし|けど|でも|むしろ")
@dataclass(frozen=True)
class PriorityState:
    state:str
    axes:dict
    components:tuple
    relation:str
    priority_rule:str
    primary_emotion:str
    secondary_emotions:tuple
    response_strategy:str
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):
        d=asdict(self)
        d["components"]=[c.snapshot() for c in self.components]
        d["secondary_emotions"]=list(self.secondary_emotions)
        return d

def detect_priority(text):
    source=str(text or "")
    base=detect_multi(source)
    if base is None:return None
    connectors=list(CONNECTOR.finditer(source))
    # First analyze the existing components; preserve v0.9.7.41 if no
    # contrastive pair exists.
    if not connectors:
        return PriorityState(base.state,dict(base.axes),base.components,
            base.relation,"NONE",None,(),base.response_strategy)
    operator=connectors[-1]
    before=[c for c in base.components if c.span[1]<=operator.start()]
    after=[c for c in base.components if c.span[0]>=operator.end()]
    after_explicit=[c for c in after if c.explicit]
    before_explicit=[c for c in before if c.explicit]
    # If a negated early affect is followed by an explicit assertion,
    # the explicit assertion takes precedence: NOT a mixed emotion.
    if after_explicit and before and all(c.negated for c in before):
        primary=after_explicit[-1]
        axes=dict(base.axes)
        axes[primary.axis]=primary.value
        return PriorityState(
            "POSITIVE_EXPLICIT" if primary.value>0 else "NEGATIVE_EXPLICIT",
            axes,base.components,"CONTRAST","EXPLICIT_AFTER_NEGATION",
            primary.emotion,tuple(c.emotion for c in before),
            "ACKNOWLEDGE_PRIMARY")
    if before_explicit and after_explicit:
        primary=after_explicit[-1]
        earlier=before_explicit[-1]
        # Opposing emotions on one axis: keep both, but express the
        # later one's sign at neutral magnitude.
        opposite=(primary.axis==earlier.axis and primary.value*earlier.value<0)
        axes=dict(base.axes)
        axes[primary.axis]=(0.25 if primary.value>0 else -0.25) if opposite else primary.value
        return PriorityState(
            ("POSITIVE_LEANING_NEUTRAL" if primary.value>0 else "SADNESS_LEANING_NEUTRAL")
              if opposite else "CONTRAST_PRIMARY",
            axes,base.components,"CONTRAST","POST_CONTRAST_DOMINANT",
            primary.emotion,tuple(c.emotion for c in base.components if c is not primary),
            "ACKNOWLEDGE_PRIMARY_AND_SECONDARY")
    return PriorityState(base.state,dict(base.axes),base.components,
         base.relation,"NONE",None,(),base.response_strategy)

def safe_response(state):
    if state is None:return None
    if state.priority_rule=="EXPLICIT_AFTER_NEGATION":
        if state.primary_emotion=="JOY":return "悲しいわけではなく、嬉しいんだね。"
        return "そうではなく、別の気持ちなんだね。"
    if state.priority_rule=="POST_CONTRAST_DOMINANT":
        pair=(state.primary_emotion,set(state.secondary_emotions))
        if pair[0]=="SADNESS" and "JOY" in pair[1]:
            return "嬉しさもあるけれど、悲しい気持ちが強いんだね。"
        if pair[0]=="JOY" and "SADNESS" in pair[1]:
            return "悲しさもあるけれど、嬉しい気持ちが強いんだね。"
        if pair[0]=="FATIGUE" and "JOY" in pair[1]:
            return "楽しかったけれど、疲れたんだね。"
        return "両方の気持ちがあるけれど、後の気持ちが大きいんだね。"
    return None
