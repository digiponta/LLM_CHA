"""v0.5.27: conservative causal direction check for sensitivity WHY questions.

A causal marker alone does not establish that the *effect* is the
requested sensitivity. Avoid matching enabling applications (MRI).
Restricted heuristic, not general causal entailment.
"""
import re

EFFECT_MARKERS=("によって","により","ことで","ため","その結果")
DOWNSTREAM=("撮像","画像","MRI","診断","測定が可能","実用化","実用的","導入","利用","応用")
SENSITIVITY=("感度","高感度","微弱な磁場","弱い磁場","小さな磁場")
MECHANISM=("量子干渉","ジョセフソン","磁束量子","磁束変化","超伝導")

def check_direction(question,sentence,kind):
    if kind!="MECHANISM" or not any(t in question for t in ("なぜ","どうして","理由","仕組み","原理")):
        return {"supported":True,"reason":"OUT_OF_SCOPE"}
    if not any(t in question for t in ("高感度","感度が高","感度の高","微弱な磁場")):
        return {"supported":True,"reason":"OUT_OF_SCOPE"}
    if not isinstance(sentence,str):
        return {"supported":False,"reason":"INVALID_EVIDENCE"}
    positions=[(sentence.find(t),t) for t in EFFECT_MARKERS if t in sentence]
    if not positions:return {"supported":False,"reason":"NO_CAUSAL_LINK"}
    pos,token=min(positions)
    cause=sentence[:pos]
    effect=sentence[pos+len(token):]
    if any(x in effect for x in DOWNSTREAM):
        return {"supported":False,"reason":"CAUSAL_DIRECTION_MISMATCH"}
    if not any(x in cause for x in MECHANISM):
        return {"supported":False,"reason":"CAUSE_NOT_PHYSICAL_MECHANISM"}
    if not any(x in effect for x in SENSITIVITY):
        return {"supported":False,"reason":"SENSITIVITY_NOT_EFFECT"}
    return {"supported":True,"reason":"CAUSE_TO_SENSITIVITY_HEURISTIC"}
