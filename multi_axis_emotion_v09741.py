"""Multi-axis affect semantics v0.9.7.41: preserve coexisting feelings.

Experimental symbolic interpretation of user text, not a measurement of
psychological state. No model, memory, or runtime mutations.
"""
import re
from dataclasses import dataclass,asdict
from continuous_emotion_semantics_v09740 import NEGATED,EXPLICIT

# Additional independent axis. Negative indicates fatigue, positive energy.
ADDITIONAL=[
 (r"疲れた|疲れている|くたくた|ぐったり|へばった","FATIGUE_ENERGY",-0.75,"FATIGUE"),
 (r"元気だ|元気いっぱい","FATIGUE_ENERGY",0.75,"ENERGY"),
]
CONTRAST=re.compile(r"けど|けれど|のに|一方|でも|むしろ")
@dataclass(frozen=True)
class EmotionComponent:
    axis:str
    value:float
    emotion:str
    negated:bool
    explicit:bool
    span:tuple
    def snapshot(self):
        d=asdict(self);d["span"]=list(self.span);return d

@dataclass(frozen=True)
class MultiAxisState:
    state:str
    axes:dict
    components:tuple
    relation:str
    response_strategy:str
    provenance:str="USER_UTTERANCE"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):
        d=asdict(self)
        d["components"]=[x.snapshot() for x in self.components]
        return d

def _nonoverlap(hits):
    # Prefer longest negation span and mask it before explicit detection.
    accepted=[]
    for start,end,axis,value,emotion,negated in sorted(hits,key=lambda h:(h[0],-(h[1]-h[0]))):
        if any(start<x[1] and end>x[0] for x in accepted):continue
        accepted.append((start,end,axis,value,emotion,negated))
    return accepted

def detect_multi(utterance):
    text=str(utterance or "").strip()
    if not text:return None
    candidates=[]
    for pattern,axis,emotion,value in NEGATED:
        for match in re.finditer(pattern,text):
            candidates.append((match.start(),match.end(),axis,value,emotion,True))
    negative=_nonoverlap(candidates)
    # Exclude negated spans from positive and other explicit matching.
    excluded=list(negative)
    explicit=[]
    for pattern,axis,value,emotion in list(EXPLICIT)+ADDITIONAL:
        for match in re.finditer(pattern,text):
            start,end=match.span()
            if any(start<x[1] and end>x[0] for x in excluded):continue
            explicit.append((start,end,axis,value,emotion,False))
    explicit=_nonoverlap(explicit)
    all_hits=sorted(negative+explicit,key=lambda h:h[0])
    if not all_hits:return None
    parts=tuple(EmotionComponent(axis,value,emotion,negated,not negated,(start,end))
        for start,end,axis,value,emotion,negated in all_hits)
    axes={}
    for p in parts:axes.setdefault(p.axis,[]).append(p.value)
    # An axis containing opposite explicit feelings cannot be collapsed.
    # Preserve its separate components and return an axis value of None.
    resolved={}
    for axis,values in axes.items():
        if min(values)<0<max(values) and any(p.explicit and p.axis==axis for p in parts):
            resolved[axis]=None
        else:
            resolved[axis]=round(sum(values)/len(values),2)
    has_explicit=any(p.explicit for p in parts)
    has_negation=any(p.negated for p in parts)
    relation="CONTRAST" if CONTRAST.search(text) and len(parts)>1 else ("AND" if len(parts)>1 else "SINGLE")
    state=("MIXED" if has_explicit and len(parts)>1 else
           "MULTI_AXIS_NEUTRAL" if has_negation and len(parts)>1 and not has_explicit else
           "NEGATED" if has_negation and not has_explicit else
           "EXPLICIT")
    strategy=("ACKNOWLEDGE_BOTH" if state=="MIXED" else
              "ACKNOWLEDGE_MULTI_NEGATION" if state=="MULTI_AXIS_NEUTRAL" else
              "ACKNOWLEDGE_NEGATION" if state=="NEGATED" else "ACKNOWLEDGE_EXPLICIT")
    return MultiAxisState(state,resolved,parts,relation,strategy)

def safe_response(state):
    if state is None:return None
    names={x.emotion for x in state.components if x.explicit}
    if "ENJOYMENT" in names and "FATIGUE" in names:
        return "楽しかったけれど、疲れたんだね。"
    if "JOY" in names and "FATIGUE" in names:
        return "楽しい時間だったけれど、疲れたんだね。"
    if "JOY" in names and "SADNESS" in names:
        return "嬉しさと悲しさの両方があるんだね。"
    if state.state=="MULTI_AXIS_NEUTRAL":
        if {x.emotion for x in state.components}=={"SADNESS","ANXIETY"}:
            return "悲しくも不安でもないんだね。"
        return "そのどちらの気持ちでもないんだね。"
    if state.state=="NEGATED":
        src=state.components[0].emotion
        return {"SADNESS":"悲しいわけではないんだね。",
                "JOY":"嬉しい気持ちではないんだね。",
                "ENJOYMENT":"楽しい気持ちではなかったんだね。",
                "ANXIETY":"不安ではないんだね。",
                "ANGER":"怒っているわけではないんだね。"}.get(src)
    if state.state=="MIXED":return "いくつかの気持ちが重なっているんだね。"
    return None
