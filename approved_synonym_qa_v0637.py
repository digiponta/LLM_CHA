"""v0.6.37: conservative approved-synonym QA router.

Only lexical equivalences from SynonymLexicon are candidates. Never treats
RELATED, BROADER or Wikipedia evidence as approved answers.
"""
from evaluate_memory_first_v0635 import norm

def approved_qa_lookup(question, overlay, lexicon, max_candidates=32):
    text=norm(question)
    direct=overlay.get(text)
    if direct:
        return {"answer":direct["answer"],"source_id":direct["source_id"],
                "route":"APPROVED_QA_OVERLAY","matched_question":text}
    if not text or max_candidates<1:
        return None
    # Single explicitly registered alias substitution; no fuzzy search.
    keys=sorted(lexicon.edges, key=lambda term:(-len(term),term))
    candidates=set()
    for term in keys:
        if term not in text:
            continue
        for alias in lexicon.expand(term,limit=8):
            if alias==term:
                continue
            candidate=norm(text.replace(term,alias))
            if candidate!=text:
                candidates.add(candidate)
            if len(candidates)>max_candidates:
                return None  # fail closed on excessive ambiguity
    matches=[(key,overlay[key]) for key in sorted(candidates) if key in overlay]
    if not matches:
        return None
    # Different approved answers, even from different sources, are ambiguous.
    if len({row["answer"] for _,row in matches})!=1:
        return None
    key,row=matches[0]
    return {"answer":row["answer"],"source_id":row["source_id"],
            "route":"APPROVED_SYNONYM_QA","matched_question":key}
