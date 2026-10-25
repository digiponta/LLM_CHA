"""Fail-closed Semantic Response Quality Gate, v0.9.7.44.

Lexical contradiction checks are conservative, not a semantic judge.
Experimental sidecar only: does not change chat.py or checkpoints.
"""
from dataclasses import dataclass,asdict
from emotion_response_plan_v09743 import plan as make_plan
from contrast_priority_emotion_v09742 import detect_priority
from multi_axis_emotion_v09741 import safe_response as multi_response,detect_multi

CUES={
 "JOY":("嬉し","うれし","楽し","良かった","よかった","満足"),
 "SADNESS":("悲し","寂し","つら","辛い","切ない"),
 "FATIGUE":("疲れ","お疲れ","休","くたくた"),
 "ANXIETY":("不安","心配"),
 "ANGER":("怒","腹が立"),
}
OPPOSITES={"JOY":"SADNESS","SADNESS":"JOY"}
INVALID=("�","FTP@","糖衣|","曼し","疲しい")
NEGATIONS=("ない","なく","ではない","じゃない","なかった","わけではない")
SAFE_SINGLE={
 "JOY":"楽しかったんだね。良かった。",
 "SADNESS":"悲しい気持ちなんだね。",
 "FATIGUE":"疲れたんだね。少し休めるといいね。",
 "ANXIETY":"不安な気持ちなんだね。",
 "ANGER":"怒りを感じているんだね。",
}

@dataclass(frozen=True)
class GateResult:
    decision:str
    reason:str
    selected_response:str
    generated_response:str
    fallback_response:str
    primary_emotion:str
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def _has(text,emotion):
    return any(w in text for w in CUES.get(emotion,()))

def fallback(text,p=None):
    p=p if p is not None else make_plan(text)
    if p is None:return None
    if p.response:return p.response
    state=detect_priority(text)
    if state and state.state=="EXPLICIT" and p.primary_emotion in SAFE_SINGLE:
        if "どうすれば" in text or "どうしたら" in text:
            return SAFE_SINGLE[p.primary_emotion]+" 話せる範囲で、何があったか教えて。"
        return SAFE_SINGLE[p.primary_emotion]
    return multi_response(detect_multi(text))

def assess(utterance,generated):
    p=make_plan(utterance)
    output=str(generated or "").strip()
    safe=fallback(utterance,p)
    if p is None or safe is None:
        return GateResult("ABSTAIN","no-safe-plan",output,output,"",
                          p.primary_emotion if p else None)
    def reject(reason):
        return GateResult("FALLBACK",reason,safe,output,safe,p.primary_emotion)
    if not output or len(output)>100 or any(x in output for x in INVALID):
        return reject("malformed-generation")
    if len(output)<5:return reject("short-fragment")
    state=detect_priority(utterance)
    components=state.components if state else ()
    # Do not infer an asserted positive emotion solely from a negation.
    for c in components:
        if c.negated and _has(output,c.emotion):
            if not any(n in output for n in NEGATIONS):
                return reject("negated-emotion-reasserted")
    primary=p.primary_emotion
    if primary is not None:
        opposite=OPPOSITES.get(primary)
        if opposite and _has(output,opposite) and not _has(output,primary):
            return reject("polarity-reversal")
        if not _has(output,primary):
            return reject("primary-emotion-not-demonstrated")
        for secondary in p.secondary_emotions:
            if not _has(output,secondary):
                return reject("secondary-emotion-not-demonstrated")
    # If the utterance is only a negation or multi-negation, require
    # explicit mention and negation markers for every negated component.
    if primary is None and any(c.negated for c in components):
        for c in components:
            if c.negated and not _has(output,c.emotion):
                return reject("negation-content-missing")
        if not any(n in output for n in NEGATIONS):
            return reject("negation-not-preserved")
    return GateResult("ACCEPT","lexical-requirements-met",output,output,safe,primary)
