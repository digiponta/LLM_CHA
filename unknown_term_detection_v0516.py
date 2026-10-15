"""v0.5.16 conservative unknown-term candidate detection for casual Japanese.

Detection is diagnostic only: no web access, memory promotion, or training.
BPE unknown tokens alone are not evidence of unknown concepts.
"""
import re

KNOWN={"AI","LLM","GPU","CUDA","映画","音楽","アベンジャーズ","量子センサー"}
STOP={"You","AI","LLM_CHA","HTTP","HTTPS","URL"}
LATIN=re.compile(r"(?<![A-Za-z0-9_])[A-Za-z][A-Za-z0-9+_-]{2,30}(?![A-Za-z0-9_])")
QUOTED=re.compile(r"[「『]([^」』]{2,32})[」』]")
TECH=re.compile(r"(?:[一-龥ァ-ヶ]{2,20}(?:センサー|理論|素子|方式))")

def detect(text,known=None,limit=5):
    if type(limit)!=int or not 1<=limit<=20:raise ValueError("invalid limit")
    known=set(KNOWN if known is None else known)
    candidates=[]
    for regex in (QUOTED,LATIN,TECH):
        for match in regex.finditer(text):
            term=(match.group(1) if regex is QUOTED else match.group(0)).strip()
            if term in known or term in STOP or term in candidates:continue
            if term.isascii() and term.islower():continue
            candidates.append(term)
            if len(candidates)>=limit:return candidates
    return candidates

def probe(text,known=None):
    terms=detect(text,known=known)
    return {"version":"v0.5.16","terms":terms,
       "lookup_required":bool(terms),"retrieved":False,
       "verified":False,"train_ready":False}
