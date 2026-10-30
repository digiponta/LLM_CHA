"""Experimental aliases and answer-value normalisation, not factual verification."""
import re
ALIASES={"スファレライト":"閃亜鉛鉱","sphalerite":"閃亜鉛鉱",
         "中央処理装置":"CPU","中央演算処理装置":"CPU"}
COMPOSITIONS={"閃亜鉛鉱":(("硫化亜鉛","ZnS"),),"水":(("H2O","H2O"),("水素と酸素の化合物","H2O"))}
def canonical_subject(text):
    value=str(text or "").strip()
    for alias,canonical in sorted(ALIASES.items(),key=lambda x:-len(x[0])):
        if alias.casefold() in value.casefold():return canonical
    return value

def composition_value(subject,sentence):
    canonical=canonical_subject(subject)
    text=str(sentence or "")
    variants=COMPOSITIONS.get(canonical,())
    # Only return a value if the sentence actually contains an explicit expression.
    for surface,value in variants:
        if surface in text:
            return {"canonical_value":value,"surface_value":surface,
                    "subject":canonical,"method":"EXPLICIT_SURFACE_ALIAS"}
    return None

def matches_subject(question,source_title,excerpt):
    canonical=canonical_subject(source_title)
    q=canonical_subject(question)
    if canonical in q:return True
    return bool(canonical and any(alias in str(question) for alias,can in ALIASES.items() if can==canonical)
                and (canonical in str(excerpt) or source_title==canonical))

def diagnose(question,evidence):
    source_title=evidence.get("topic","")
    excerpt=str(evidence.get("excerpt",""))
    subject_match=matches_subject(question,source_title,excerpt)
    result={"question":question,"source_title":source_title,
            "canonical_subject":canonical_subject(source_title),
            "subject_match":subject_match,"composition_candidates":[]}
    if not subject_match:return result
    for sentence in re.split(r"(?<=。)",excerpt):
        if len(sentence.strip())<10:continue
        found=composition_value(source_title,sentence)
        if found:result["composition_candidates"].append({**found,"sentence":sentence.strip()})
    return result
