"""Conservative quality checks for corpus evidence and ungrounded chat replies."""
import re

def evidence_score(sentence, label):
    s=str(sentence or "").strip()
    if len(s)<24:
        return -1
    terms={"粒子と波動":("波動","波として"),"エネルギー準位":("順位","準位"),
           "零点エネルギー":("零点エネルギー",)}.get(label,(label,))
    if not any(term in s for term in terms):
        return -1
    if not any(x in s for x in ("。","！","？")):
        return -1
    if any(x in s for x in ("かもしれない","アナロジ")):
        penalty=2
    else:
        penalty=0
    return len([t for t in terms if t in s])*10+min(len(s),160)/20-penalty

def best_evidence(sentences,label):
    scored=sorted(((evidence_score(s,label),s) for s in sentences),reverse=True)
    return scored[0][1] if scored and scored[0][0]>=0 else None

def generation_quality(question,reply):
    q=str(question or "").strip()
    a=str(reply or "").strip()
    if q in ("貴方はどう思う","貴方はどう思う？","あなたはどう思う","あなたはどう思う？","どう思う","どう思う？"):
        if len(a)<8 or not any(x in a for x in ("思","考","感じ","判断","意見","情報","説明")):
            return {"accepted":False,"reason":"UNSUPPORTED_SHORT_OPINION",
                    "fallback":"その話題について、どの点への意見が必要？ 具体的に聞いて。"}
    if a in ("有希広","未学習です") and q.endswith("どう思う？"):
        return {"accepted":False,"reason":"MALFORMED_REPLY",
                "fallback":"もう少し具体的に聞いて。"}
    return {"accepted":True,"reason":"NO_SPECIFIC_DEFECT_DETECTED","fallback":None}
