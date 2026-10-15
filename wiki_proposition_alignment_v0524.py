"""v0.5.24 restricted semantic proposition alignment for Wiki evidence.

This parser is conservative and domain-limited, not a general NLP entailment
model. Unknown subjects and polarity fail closed for sensitivity questions.
"""
import re

VARIANT=re.compile(r"(?<![A-Za-z0-9_])(RF|DC|AC)\s*SQUID(?![A-Za-z0-9_])",re.I)
LOW=re.compile(r"(?:感度|感受性)(?:は|が|の)?(?:非常に|比較的)?(?:低い|低く|劣る)|低感度|感度を犠牲")
HIGH=("高感度","感度が高","微弱な磁場","弱い磁場","小さな磁場")

def proposition(text,default_subject=None):
    m=VARIANT.search(text)
    subject=(m.group(1).upper()+" SQUID") if m else (
        "SQUID" if "SQUID" in text or "超伝導量子干渉計" in text else default_subject)
    polarity="LOW" if LOW.search(text) else ("HIGH" if any(x in text for x in HIGH) else "UNKNOWN")
    cause=any(x in text for x in ("によって","により","ことで","ため","その結果"))
    mechanism=any(x in text for x in ("量子干渉","ジョセフソン","磁束量子","超伝導"))
    return {"subject":subject,"predicate":"sensitivity" if any(x in text for x in ("感度","磁場","磁気")) else None,
            "object":polarity,"condition":"variant" if m else None,
            "polarity":polarity,"cause":cause,"mechanism":mechanism}

def align(question,evidence,kind,subject=None):
    q=proposition(question,default_subject=subject)
    e=proposition(evidence,default_subject=None)
    if kind!="MECHANISM" or not any(x in question for x in ("高感度","感度が高","感度の高","微弱な磁場")):
        return {"aligned":True,"reason":"OUT_OF_SCOPE","question":q,"evidence":e}
    if q["subject"] is None or e["subject"] is None:
        reason="UNKNOWN_SUBJECT"
    elif q["subject"]!=e["subject"]:
        reason="SUBJECT_MISMATCH"
    elif q["polarity"]=="HIGH" and e["polarity"]!="HIGH":
        reason="POLARITY_MISMATCH"
    elif not(e["cause"] and e["mechanism"]):
        reason="CAUSAL_RELATION_UNSUPPORTED"
    else:
        reason="ALIGNED"
    return {"aligned":reason=="ALIGNED","reason":reason,"question":q,"evidence":e}
