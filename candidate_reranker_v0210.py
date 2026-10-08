"""v0.2.10 deterministic pre-gate ranking for conversational generated candidates.

Ranking never accepts a candidate: all existing semantic/unknown gates still run
on the selected primary and on the same generated probe set.
"""
from __future__ import annotations
from conversation_diagnostics_v026 import classify_quality
from dialogue_state_v029 import repeat_check

def rank_candidates(question, results, history, *, min_confidence=.18, min_token_confidence=.02, min_margin=.01):
    if not results:return list(results), []
    scored=[]
    for index,item in enumerate(results):
        text=item.text or ""
        diag=classify_quality(question,text)
        repetition, similarity=repeat_check(question,text,history)
        valid=(bool(text.strip()) and item.mean_confidence>=min_confidence
               and item.min_confidence>=min_token_confidence
               and item.mean_top2_margin>=min_margin
               and not diag["flag"] and not repetition)
        # Penalize obvious generic replies; prefer substantive but not arbitrarily long text.
        # The original greedy output wins ties.
        score=(min(len(text.strip()),80)*.005
               + min(item.mean_confidence,1)*.25
               - (0.6 if diag["generic"] else 0)
               - (0.8 if repetition else 0)
               - (0.3 if diag["context_required"] and diag["short"] else 0))
        scored.append({"index":index,"valid":valid,"score":round(score,5),
                       "repetition":repetition,"repeat_similarity":round(similarity,3),
                       "generic":diag["generic"],"text":text})
    eligible=[r for r in scored if r["valid"]]
    if not eligible:return list(results),scored
    best=max(eligible,key=lambda r:(r["score"],-r["index"]))["index"]
    if best==0:return list(results),scored
    return [results[best]]+[r for i,r in enumerate(results) if i!=best],scored
