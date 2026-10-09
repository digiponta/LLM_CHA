"""v0.2.20 deterministic context-aware candidate ranking.

Pre-gate only: the semantic, unknown, truth and quality gates retain authority.
"""
from __future__ import annotations
import re
from conversation_diagnostics_v026 import classify_quality
from dialogue_state_v029 import repeat_check

SHORT_ACK = {"そう","そうです","そうなんだ","そうなんですね","なるほど","はい","うん","へえ","そうですね","わかった","了解"}
STOP = {"最近","その話","続けて","について","です","ます","して","いる","読んで","聞いて"}
def cleaned(s):
    return re.sub(r"[\s。！？?!、,.]+","",s or "")
def topic_terms(question,history):
    source=question+" "+" ".join(q for q,_ in history[-2:])
    chunks=re.findall(r"[A-Za-z]{2,}|[一-龥]{2,}|[ァ-ヶー]{2,}",source)
    return [s for s in dict.fromkeys(chunks) if s not in STOP and len(s)>=2]
def score_candidate(question,item,history,idx,conf=.18,tok=.02,margin=.01):
    text=(item.text or "").strip()
    diag=classify_quality(question,text)
    repeated,sim=repeat_check(question,text,history)
    acknowledgement=cleaned(text) in SHORT_ACK or len(cleaned(text))<=3
    terms=topic_terms(question,history)
    overlap=sum(1 for x in terms if x in text)
    unsupported_claim=bool(re.search(r"(必ず|絶対|確実に|事実です)",text))
    valid=bool(text) and item.mean_confidence>=conf and item.min_confidence>=tok and item.mean_top2_margin>=margin and not diag["flag"] and not repeated
    score=(min(len(text),80)*.008+min(item.mean_confidence,1)*.25+
           min(overlap,3)*.15-(.9 if acknowledgement else 0)-
           (.6 if diag["generic"] else 0)-(.8 if repeated else 0)-
           (.2 if unsupported_claim else 0))
    return {"index":idx,"valid":valid,"score":round(score,5),
            "repetition":repeated,"repeat_similarity":round(sim,3),
            "generic":diag["generic"],"acknowledgement":acknowledgement,
            "topic_overlap":overlap,"text":text}
def rank_candidates(question,results,history,*,min_confidence=.18,min_token_confidence=.02,min_margin=.01):
    if not results:return list(results),[]
    scored=[score_candidate(question,r,history,i,min_confidence,min_token_confidence,min_margin) for i,r in enumerate(results)]
    eligible=[r for r in scored if r["valid"]]
    if not eligible:return list(results),scored
    selected=max(eligible,key=lambda r:(r["score"],-r["index"]))["index"]
    return [results[selected]]+[r for i,r in enumerate(results) if i!=selected],scored
