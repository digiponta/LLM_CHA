"""v0.3.7.1 source-grounded Persona Semantic Memory (read-only).

A character's opinions are NOT assertions of scientific truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

@dataclass(frozen=True)
class PersonaEvidence:
    id: str
    concept: str
    excerpt: str
    source: str
    line: int
    segment: int
    epistemic_type: str = "PERSONA_STATEMENT"
    factual_truth: str = "NOT_ASSESSED"

def segments(line: str):
    return [p.strip() for p in re.split(r"[。！？!?]",line) if p.strip()]

def evidence(source: str | Path, concept: str, limit: int = 3):
    concept=concept.strip()
    if not concept or len(concept)>100 or "\n" in concept or "\r" in concept:
        raise ValueError("invalid concept")
    if limit<1 or limit>30:raise ValueError("limit must be 1..30")
    source=Path(source)
    result=[]
    for lineno,line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(),1):
        for ordinal,fragment in enumerate(segments(line),1):
            if concept not in fragment:continue
            digest=sha256(f"{source}:{lineno}:{ordinal}:{fragment}".encode()).hexdigest()[:24]
            result.append(PersonaEvidence(digest,concept,fragment,str(source),lineno,ordinal))
            if len(result)>=limit:return result
    return result

def persona_reply(source: str | Path, concept: str, limit: int = 2):
    hits=evidence(source,concept,limit)
    if not hits:
        return f"この人格の原文には「{concept}」についての記述が見つかりません。",[]
    if len(hits)==1:
        prose=f"この人格の原文には、次の考えが記されています。「{hits[0].excerpt}」"
    else:
        prose="この人格の原文には、次のような考えが記されています。" + "".join(
            f"\n・「{row.excerpt}」" for row in hits
        )
    return prose,hits
