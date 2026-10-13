"""v0.4.18 conservative nominal-ending definition extraction.

Only used after v0.4.12 produced no definitions. Exact literal spans;
Wikipedia text remains UNVERIFIED, non-trainable and review-pending.
"""
from __future__ import annotations
import re
from article_proposition_alignment_v0412 import align as baseline, SENTENCE, _find_subject_marker, BLOCK

NOMINAL_ENDINGS=("の一部門","の一分野","の一領域","の一種","の一つ","の一形式","の一部","の学問")
CONTEXT_GUARDS=("しかし","ただし","仮に","もし","例えば","とされる","と言われる",
                "と考えられる","という説","かもしれない","らしい","と仮定")
def align(evidence):
    result=baseline(evidence)
    if result["propositions"]:
        result["v0418_nominal_added"]=0
        return result
    text=evidence["lead_extract"]
    topic=evidence["concept"].strip()
    props=[]
    for match in SENTENCE.finditer(text):
        segment=match.group()
        sentence=segment.strip()
        if not sentence.endswith("。"):continue
        if len(sentence)>280 or len(sentence)<10:continue
        # Explicit topic + definition marker required, never 'Xは広大' properties.
        marker=_find_subject_marker(sentence,topic)
        if marker is None or not sentence.startswith("とは",len(topic)) and not (
            sentence.startswith("（",len(topic)) and "とは" in sentence[:marker]):
            continue
        predicate=sentence[marker:-1].strip()
        if not predicate.endswith(NOMINAL_ENDINGS):continue
        if not (4<=len(predicate)<=240):continue
        if any(g in predicate for g in BLOCK+CONTEXT_GUARDS):continue
        if any(ch in sentence for ch in ("「","」","『","』","？","！","?","!")):continue
        start=match.start()+len(segment)-len(segment.lstrip())
        end=start+len(sentence)
        if text[start:end]!=sentence:raise ValueError("evidence span mismatch")
        props.append({"subject":topic,"predicate":predicate,
                      "proposition_literal":sentence,"evidence_start":start,"evidence_end":end,
                      "evidence_text":sentence,"alignment":"EXACT_LITERAL_SPAN",
                      "pattern":"EXPLICIT_TOPIC_NOMINAL_CLASSIFICATION",
                      "factual_truth":"UNVERIFIED","review_state":"PENDING_REVIEW",
                      "eligible_for_training":False})
    result.update(version="v0.4.18",alignment_type="GUARDED_NOMINAL_ENDING",
                  propositions=props,proposition_count=len(props),
                  v0418_nominal_added=len(props))
    return result
