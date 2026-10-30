"""Non-authoritative, diagnostic-only comparison of an LLM candidate and source.

Lexical overlap cannot prove entailment. No auto-approval or learning.
"""
import re
from difflib import SequenceMatcher

def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[。！？!?])|[\r\n]+",text or "") if s.strip()]

def analyze(candidate,evidence,gate):
    source=str(evidence.get("excerpt",""))
    candidate=str(candidate or "").strip()
    parts=sentences(candidate)
    source_parts=sentences(source)
    metrics=[]
    for part in parts:
        sims=[SequenceMatcher(None,part,src).ratio() for src in source_parts]
        exact=part.rstrip("。！？!?") in source if len(part)>=8 else False
        metrics.append({"candidate":part[:300],"exact_source_substring":exact,
                        "best_sentence_similarity":round(max(sims,default=0.0),3)})
    return {"topic":str(evidence.get("topic","")),"source_url":str(evidence.get("url","")),
            "source_excerpt":source[:900],"candidate":candidate[:900],
            "gate":gate,"candidate_sentences":metrics,
            "interpretation":"Diagnostic lexical comparison only; no semantic entailment verified."}
