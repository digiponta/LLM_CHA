"""v0.5.23 conservative polarity/subject alignment for Wiki evidence.

Not a general entailment model. Fail closed when a sensitivity WHY question
receives evidence about lower sensitivity, cost, or a different SQUID variant.
"""
import re

def check(question,sentence,kind):
    result={"supported":True,"reason":"NO_APPLICABLE_POLARITY_RULE"}
    if kind!="MECHANISM" or not any(x in question for x in ("高感度","感度が高","感度の高","微弱な磁場")):
        return result
    low=bool(re.search(r"(?:感度|感受性)(?:は|が|の)?(?:非常に|比較的)?(?:低い|低く|劣る)|低感度|感度を犠牲",sentence))
    variant=bool(re.search(r"\b(?:RF|DC|AC)\s*SQUID\b",sentence,re.I))
    if variant:
        return {"supported":False,"reason":"SUBJECT_VARIANT_MISMATCH"}
    if low:
        return {"supported":False,"reason":"POLARITY_MISMATCH"}
    positive=any(x in sentence for x in ("高感度","感度が高","感度を高","微弱な磁場","弱い磁場","小さな磁場"))
    causal=any(x in sentence for x in ("ため","によって","により","ことで","その結果"))
    mechanism=any(x in sentence for x in ("量子干渉","ジョセフソン","磁束量子","超伝導"))
    if not (positive and causal and mechanism):
        return {"supported":False,"reason":"CAUSAL_TARGET_NOT_ESTABLISHED"}
    return {"supported":True,"reason":"TARGET_POLARITY_CAUSAL_HEURISTIC"}
