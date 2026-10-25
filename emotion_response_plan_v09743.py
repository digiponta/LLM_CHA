"""Bridge contrast-priority Semantic State to controlled response strategy.

Diagnostics only: model training, live routing and Semantic Memory untouched.
"""
from dataclasses import dataclass,asdict
from contrast_priority_emotion_v09742 import detect_priority
from multi_axis_emotion_v09741 import safe_response as multi_safe
from multi_axis_emotion_v09741 import detect_multi

@dataclass(frozen=True)
class ResponsePlan:
    primary_emotion:str
    primary_emotion_value:float
    overall_emotion_value:float
    overall_axis:str
    secondary_emotions:tuple
    response_strategy:str
    response:str
    reason:str
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):
        d=asdict(self);d["secondary_emotions"]=list(self.secondary_emotions);return d

def plan(text):
    state=detect_priority(text)
    if state is None:return None
    explicit=[c for c in state.components if c.explicit]
    primary=next((c for c in reversed(explicit) if c.emotion==state.primary_emotion),None)
    if primary is None and len(explicit)==1:primary=explicit[0]
    primary_name=primary.emotion if primary is not None else None
    primary_value=primary.value if primary is not None else None
    secondary=[]
    for c in explicit:
        if c.emotion!=primary_name and c.emotion not in secondary:
            secondary.append(c.emotion)
    axis=primary.axis if primary else (next(iter(state.axes)) if len(state.axes)==1 else None)
    overall=state.axes.get(axis) if axis else None
    strategy=state.response_strategy
    if state.priority_rule=="EXPLICIT_AFTER_NEGATION":
        response={"JOY":"嬉しいんだね。良かった。","SADNESS":"悲しい気持ちなんだね。"}.get(primary_name)
        reason="explicit-after-negation"
    elif state.priority_rule=="POST_CONTRAST_DOMINANT":
        pairs={
          ("SADNESS","JOY"):"嬉しさもあるけれど、悲しい気持ちが強いんだね。",
          ("JOY","SADNESS"):"悲しさもあるけれど、嬉しい気持ちが強いんだね。",
          ("FATIGUE","JOY"):"楽しかったけれど、疲れたんだね。",
        }
        response=next((pairs.get((primary_name,s)) for s in secondary if (primary_name,s) in pairs),None)
        reason="post-contrast"
    else:
        response=multi_safe(detect_multi(text))
        reason="multi-axis-fallback"
    return ResponsePlan(primary_name,primary_value,overall,axis,tuple(secondary),
                        strategy,response,reason)
