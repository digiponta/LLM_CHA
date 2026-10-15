"""v0.5.22 conservative question/evidence answerability classification.

Rules explicitly reject dictionary-style definitions as APPLICATION and
component mentions as MECHANISM. This is NOT neural entailment verification.
"""
import re

DEFINITION=("とは","の一種","である","と呼ばれる")
APPLICATION=("医療","脳磁","心磁","地質","研究","診断","材料","産業","用途","応用")
USE_VERBS=("利用され","使用され","使われ","用いられ","活用され","応用され","利用する","使用する")
CAUSE=("によって","により","ため","ことで","その結果","したがって")
MECHANISM=("量子干渉","磁束量子","ジョセフソン","超伝導","干渉","磁場","磁束")
SENSITIVITY=("高感度","感度","微弱","小さな","弱い","精度","検出")

def evaluate(sentence,kind,question=""):
    if not isinstance(sentence,str) or not 15<=len(sentence)<=240:
        return {"answerable":False,"reason":"INVALID_EVIDENCE"}
    if kind=="APPLICATION":
        # Merely saying 'used to detect weak fields' in a definition is not
        # a concrete application of the device.
        application=any(w in sentence for w in APPLICATION)
        action=any(w in sentence for w in USE_VERBS)
        ok=application and action
        return {"answerable":ok,"reason":"APPLICATION_EVIDENCE" if ok else "DEFINITION_NOT_APPLICATION"}
    if kind=="MECHANISM":
        # More than naming the Josephson junction: require an explicit
        # causal construction linked to sensitivity or detection.
        causal=any(w in sentence for w in CAUSE)
        mechanism=any(w in sentence for w in MECHANISM)
        target=any(w in sentence for w in SENSITIVITY)
        ok=causal and mechanism and target
        return {"answerable":ok,"reason":"CAUSAL_EVIDENCE" if ok else "NO_CAUSAL_EXPLANATION"}
    return {"answerable":False,"reason":"UNSUPPORTED_INTENT"}
