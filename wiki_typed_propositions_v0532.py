"""v0.5.32 typed atomic propositions from explicitly supported source spans.

Conservative SQUID-style definition extraction. Not a general Japanese parser.
Each triple preserves the exact supporting span and original Wikipedia evidence.
No causality, semantic promotion or model training is inferred.
"""
import re
from wiki_proposition_decomposition_v0531 import decompose

def _record(subject,predicate,obj,kind,span,part):
    return {"subject":subject,"predicate":predicate,"object":obj,"type":kind,
            "evidence_span":span,"source":part["source"],"original":part["original"],
            "statement":part["text"],"verified":False,"train_ready":False,
            "promoted":False,"inferred_causality":False}

def extract(sentence,source=None):
    parts=decompose(sentence,source)
    records=[]
    for part in parts:
        m=re.match(r"^(.+?)とは、(.+?)。?$",part["text"])
        if not m:continue
        subject,clause=m.group(1).strip(),m.group(2).rstrip("。")
        if not subject or not clause:continue
        if part["kind"]=="STRUCTURE":
            # A device can contain Josephson junctions while being based on
            # superconducting loops; keep these as two independent facts.
            structure=re.fullmatch(r"(.+?)(?:に基く|に基づく)",clause)
            if not structure:continue
            phrase=structure.group(1)
            contained=re.fullmatch(r"(.+?)を含む(.+)",phrase)
            if contained:
                component,base=contained.groups()
                if component.strip() and base.strip():
                    records.append(_record(subject,"contains",component.strip(),"COMPONENT",
                                           component+"を含む",part))
                    records.append(_record(subject,"based_on",base.strip(),"STRUCTURE",
                                           phrase+"に基く" if clause.endswith("に基く") else phrase+"に基づく",part))
            else:
                records.append(_record(subject,"based_on",phrase.strip(),"STRUCTURE",clause,part))
        elif part["kind"]=="ROLE":
            # Do not interpret 'used to detect' as a measured performance
            # guarantee. A descriptive 'high sensitivity' is a separate claim.
            use=re.search(r"(.+?)の検出に用いられる",clause)
            if use:
                records.append(_record(subject,"detects",use.group(1).strip(),"FUNCTION",
                                       use.group(0),part))
            if "非常に感度の高い" in clause:
                records.append(_record(subject,"has_property","非常に高い感度",
                                       "PERFORMANCE","非常に感度の高い",part))
    return records

def assess(records,question):
    """Question relevance only; not an assertion of scientific entailment."""
    if not isinstance(question,str):return []
    why=any(t in question for t in ("なぜ","どうして","理由"))
    return [{**r,"answerable":not why and (
        ("構造" in question or "構成" in question) and r["type"] in ("STRUCTURE","COMPONENT")
        or ("何を検出" in question and r["type"]=="FUNCTION")
        or ("感度" in question and r["type"]=="PERFORMANCE")),
        "causal_explanation":False} for r in records]
