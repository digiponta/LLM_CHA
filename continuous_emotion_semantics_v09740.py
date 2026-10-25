"""Continuous affect-axis Semantic State v0.9.7.40 (diagnostic only).

Negation of one emotion maps to slightly opposite-leaning neutral,
not to fully asserted opposite emotion. Explicit other feelings win.
"""
import re
from dataclasses import dataclass,asdict

AXES={
    "SADNESS_JOY":{"negative":("悲しい","悲しく","寂しい","寂しく"),"positive":("嬉しい","うれしい","喜ん","楽しい","楽しかった"),"axis":"SADNESS_JOY"},
    "ANXIETY_CALM":{"negative":("不安",),"positive":("安心","落ち着"),"axis":"ANXIETY_CALM"},
    "ANGER_CALM":{"negative":("怒っ","腹が立","苛立"),"positive":("穏やか",),"axis":"ANGER_CALM"},
}
NEGATED=[
    (r"悲しく(?:は)?ない|悲しいわけではない|悲しくなんてない","SADNESS_JOY","SADNESS",0.25),
    (r"寂しく(?:は|なんて)?ない|寂しいわけではない","SADNESS_JOY","SADNESS",0.25),
    (r"嬉しく(?:は)?ない|うれしく(?:は)?ない|嬉しいわけではない","SADNESS_JOY","JOY",-0.25),
    (r"楽しく(?:は)?なかった|楽しく(?:は)?ない|楽しめなかった","SADNESS_JOY","ENJOYMENT",-0.25),
    (r"不安(?:では|じゃ|は)?ない|不安は感じない","ANXIETY_CALM","ANXIETY",0.25),
    (r"怒って(?:は)?いない|怒ってない|怒りはない","ANGER_CALM","ANGER",0.25),
]
EXPLICIT=[
    (r"嬉しい|うれしい|喜んでいる|楽しかった|楽しい","SADNESS_JOY",0.75,"JOY"),
    (r"悲しい|寂しい|つらい|辛い","SADNESS_JOY",-0.75,"SADNESS"),
    (r"不安だ|不安です|不安がある","ANXIETY_CALM",-0.75,"ANXIETY"),
    (r"安心した|安心している","ANXIETY_CALM",0.75,"CALM"),
    (r"怒っている|怒りがある","ANGER_CALM",-0.75,"ANGER"),
    (r"穏やかだ|穏やかな","ANGER_CALM",0.75,"CALM"),
]

@dataclass(frozen=True)
class AffectState:
    axis:str
    value:float
    state:str
    source_emotion:str
    negated:bool
    inferred_opposite:bool
    explicit_emotions:tuple
    strategy:str
    provenance:str="USER_UTTERANCE"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):
        d=asdict(self);d["explicit_emotions"]=list(self.explicit_emotions);return d

def _remove_spans(text,spans):
    chars=list(text)
    for a,b in spans:
        for i in range(a,b):chars[i]=" "
    return "".join(chars)

def detect_affect(utterance):
    text=str(utterance or "").strip()
    if not text:return None
    negations=[]
    for pattern,axis,emotion,value in NEGATED:
        for m in re.finditer(pattern,text):
            negations.append((m.start(),m.end(),axis,emotion,value))
    # Prevent partial overlapping regex matches from being interpreted twice.
    selected=[]
    for item in sorted(negations,key=lambda x:(x[0],-(x[1]-x[0]))):
        if any(item[0]<existing[1] and item[1]>existing[0] for existing in selected):
            continue
        selected.append(item)
    residual=_remove_spans(text,[(x[0],x[1]) for x in selected])
    explicit=[]
    for pattern,axis,value,name in EXPLICIT:
        if re.search(pattern,residual):
            explicit.append((axis,value,name))
    if explicit:
        # Any explicit contrasting emotion takes priority over weak inferred neutrality.
        dominant=explicit[-1]
        vals=[e[1] for e in explicit if e[0]==dominant[0]]
        if len(vals)>1 and min(vals)<0<max(vals):
            return AffectState(dominant[0],round(sum(vals)/len(vals),2),
                "MIXED",dominant[2],bool(selected),False,
                tuple(e[2] for e in explicit),"ACKNOWLEDGE_BOTH")
        v=dominant[1]
        return AffectState(dominant[0],v,
           "POSITIVE_EXPLICIT" if v>0 else "NEGATIVE_EXPLICIT",dominant[2],
           bool(selected),False,tuple(e[2] for e in explicit),
           "ACKNOWLEDGE_EXPLICIT")
    if selected:
        x=selected[0]
        if len(selected)>1 and any(y[2]!=x[2] for y in selected):
            # Independent axes cannot be collapsed to a single scalar.
            return None
        if any(y[4]!=x[4] for y in selected):
            return AffectState(x[2],0.0,"MIXED_NEGATIONS",x[3],True,False,(),
                               "ACKNOWLEDGE_NEGATION")
        return AffectState(x[2],x[4],
           "POSITIVE_LEANING_NEUTRAL" if x[4]>0 else "NEGATIVE_LEANING_NEUTRAL",
           x[3],True,False,(),"ACKNOWLEDGE_NEGATION")
    return None

def safe_response(state):
    if state is None:return None
    if state.state=="MIXED":return "いろいろな気持ちが重なっているんだね。"
    if state.state=="MIXED_NEGATIONS":return "どちらの気持ちとも少し違うんだね。"
    if state.negated and state.strategy=="ACKNOWLEDGE_NEGATION":
        pairs={
          ("SADNESS_JOY",True):"悲しいわけではないんだね。",
          ("SADNESS_JOY",False):"嬉しい気持ちではないんだね。",
          ("ANXIETY_CALM",True):"不安ではないんだね。",
          ("ANGER_CALM",True):"怒っているわけではないんだね。",
        }
        if state.source_emotion=="ENJOYMENT":return "楽しい気持ちではなかったんだね。"
        return pairs.get((state.axis,state.value>0),"そういう気持ちではないんだね。")
    return None
