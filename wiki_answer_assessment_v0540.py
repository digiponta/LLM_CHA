"""v0.5.40 conservative comparison of prior answer with Wikipedia evidence.

Four statuses describe *evidence support*, not objective factual truth.
"""
import re
from wiki_proposition_comparison_v0537 import collect, compare

def assess(previous_answer, evidence_span, topic, source=None):
    base={"verified":False,"train_ready":False,"promoted":False,
          "source":source,"correction_approved":False}
    if not isinstance(previous_answer,str) or not previous_answer.strip() or not isinstance(evidence_span,str) or not evidence_span.strip():
        return {**base,"status":"INSUFFICIENT","reason":"MISSING_INPUT"}
    # Require comparable structured statements to assert support or contradiction.
    old=[]
    new=[]
    for x in re.split(r"[。\n]",previous_answer):
        old.extend(collect(x.strip()+"。","MODEL_OUTPUT_UNVERIFIED"))
    for x in re.split(r"[。\n]",evidence_span):
        new.extend(collect(x.strip()+"。",source))
    for a in old:
        for b in new:
            judgment=compare(a,b)
            if judgment["status"]=="CONFLICT":
                return {**base,"status":"CONTRADICTED","reason":"EXPLICIT_ATOMIC_NEGATION",
                        "previous_proposition":a,"evidence_proposition":b}
            if judgment["status"]=="MATCH":
                return {**base,"status":"SUPPORTED","reason":"EXACT_ATOMIC_MATCH",
                        "previous_proposition":a,"evidence_proposition":b}
    # Neither lexical mismatch nor generic tokens establish falsehood.
    if old and new:
        return {**base,"status":"UNSUPPORTED","reason":"NO_MATCHING_ATOMIC_EVIDENCE"}
    return {**base,"status":"INSUFFICIENT","reason":"NOT_COMPARABLE_AS_ATOMIC_PROPOSITIONS"}
