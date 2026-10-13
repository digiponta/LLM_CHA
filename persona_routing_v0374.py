"""v0.3.7.4 persona provenance display and source-grounded ranking."""
from __future__ import annotations
from pathlib import Path
import re
from persona_semantic_memory_v0371 import evidence

def is_persona_corpus(provenance: object) -> bool:
    """Label only recognized Nagato-authored corpus evidence, not arbitrary retrieval."""
    value=str(provenance).replace("\\","/").lower()
    return "data-nagato.txt" in value and "subject-keyed-corpus-memory" in value

def answer_prefix(provenance: object) -> str:
    return "persona>" if is_persona_corpus(provenance) else "AI>"

def ranked_persona_reply(source: str | Path, concept: str, limit: int = 2):
    """Prefer complete and topic-bearing excerpts over trivial substring fragments.

    Ranking is heuristic, source-only, deterministic; no scientific validation
    and no new propositions are inferred.
    """
    items=evidence(source,concept,limit=30)
    if not items:
        return None,[]
    def relevance(row):
        sentence=row.excerpt
        length=len(sentence)
        subject_match=bool(re.search(r"(?:^|[、， ])"+re.escape(concept)+r"(?:は|が|という|とは|を|で|によって)",sentence))
        lexical_density=len(sentence.replace(concept,"").strip())
        fragment_penalty=(length<18)*10
        return (int(subject_match)*12+min(lexical_density,100)/10-fragment_penalty,
                -row.line,-row.segment)
    chosen=sorted(items,key=relevance,reverse=True)[:limit]
    intro="この人格の原文には、次のような考えが記されています。"
    return intro+"".join(f"\n・「{row.excerpt}」" for row in chosen),chosen
