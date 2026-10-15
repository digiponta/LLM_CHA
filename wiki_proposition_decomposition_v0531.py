"""v0.5.31 conservative shared-subject proposition decomposition.

Split coordinate predicates that clearly share a subject; never turn
co-occurrence or a structural description into a causal explanation.
Preserve the original source span, source URL and unverified state.
"""
import re

# Restricted to Japanese definition clauses with a shared nominal subject.
STRUCTURAL=("に基く","に基づく","からなる","で構成される")
ROLE=("に用いられる","の一種である","として利用される")
def decompose(sentence,source=None):
    if not isinstance(sentence,str):return []
    raw=sentence.strip()
    if not raw:return []
    core=raw.rstrip("。").strip()
    match=re.match(r"^(.+?とは、)(.+)$",core)
    if not match:
        return [{"text":raw,"kind":"UNSPLIT","source":source,"original":raw,
                 "inferred_causality":False,"verified":False,"train_ready":False}]
    prefix,body=match.groups()
    # Splitting requires two complete clauses, not arbitrary commas.
    split=re.match(r"^(.+?(?:に基く|に基づく|からなる|で構成される))、(.+)$",body)
    if not split or not any(term in split.group(2) for term in ROLE):
        return [{"text":raw,"kind":"UNSPLIT","source":source,"original":raw,
                 "inferred_causality":False,"verified":False,"train_ready":False}]
    structure,role=split.groups()
    parts=[("STRUCTURE",structure),("ROLE",role)]
    return [{"text":prefix+clause+"。","kind":kind,"source":source,
             "original":raw,"inferred_causality":False,
             "verified":False,"train_ready":False} for kind,clause in parts]
