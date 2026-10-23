"""v0.7.11 conservative experimental response gate and opt-in fallback.

A quality heuristic cannot establish truth. It can only reject obvious
generation failures. All accepted outputs remain EXPERIMENTAL_UNVERIFIED.
"""
import re

def quality_gate(question, answer):
    text=str(answer or "").strip()
    if not text:return False,"empty"
    if len(text)<5:return False,"too_short"
    if len(text)>450:return False,"too_long"
    if any(tag in text for tag in ("候補の実験回答","回答回答","回収録答")):
        return False,"experiment_leakage"
    # Known malformed fragments observed in the v0.7.10 pilot. This is a\n    # narrow regression guard, not a general semantic or factual validator.\n    if any(fragment in text for fragment in ("量化回", "コェル落")):\n        return False,"malformed_generation"\n    if re.search(r"(.)\1{3,}",text):
        return False,"repetition"
    if re.search(r"(.{2,10})\1{2,}",text):
        return False,"phrase_loop"
    if text.count("。")==0 and text.count("です")==0 and text.count("ます")==0:
        return False,"incomplete"
    # For a technical/named subject request, require some lexical grounding.
    q=re.sub(r"(とは|って|について|教えて|ください|何ですか|は|？|\?|です|か)","",str(question)).strip()
    if len(q)>=2 and q not in text and q not in ("こんにちは","こんばんは","おはよう"):
        return False,"ungrounded_topic"
    return True,"heuristic_only_not_truth_verified"

def fallback_on_structured_unknown(question,experimental_ask,*,allow=False):
    if not allow:
        return None
    output=experimental_ask(question)
    passed,reason=quality_gate(question,output)
    if not passed:
        return {"route":"EXPERIMENTAL_REJECTED","answer":None,
                "truth_state":"UNKNOWN","reason":reason,
                "auto_promote":False}
    return {"route":"EXPERIMENTAL_FALLBACK","answer":"【未承認・実験的回答】"+output,
            "truth_state":"EXPERIMENTAL_UNVERIFIED","reason":reason,
            "auto_promote":False}
