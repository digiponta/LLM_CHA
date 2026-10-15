"""v0.5.25: read-only semantic memory / Wikipedia evidence comparison.

Legacy Semantic Proposition rows have only subject and value. This bridge
never fabricates truth labels or auto-promotes Wikipedia/user knowledge.
Equality/contradiction are conservative lexical checks, not entailment.
"""
from pathlib import Path
from semantic_proposition_v1090 import load_propositions, normalize_fragment
from wiki_proposition_alignment_v0524 import proposition

def compare(wiki, memory_rows):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_WIKI_EVIDENCE","matches":[],"conflicts":[]}
    sentence=wiki.get("sentence") or wiki.get("extract","")
    title=wiki.get("title","")
    if not isinstance(sentence,str) or not sentence.strip():
        return {"status":"NO_WIKI_EVIDENCE","matches":[],"conflicts":[]}
    canonical="SQUID" if title=="超伝導量子干渉計" or title=="SQUID" else title
    ext=proposition(sentence,default_subject=canonical)
    matches=[]; conflicts=[]
    for row in memory_rows:
        subject=normalize_fragment(row.subject)
        value=normalize_fragment(row.value)
        if subject not in (canonical,title) or not value:continue
        local=proposition(value,default_subject=canonical)
        if ext["predicate"]=="sensitivity" and local["predicate"]=="sensitivity" and (
            ext["polarity"]!="UNKNOWN" and local["polarity"]!="UNKNOWN"):
            if ext["subject"]==local["subject"] and ext["polarity"]!=local["polarity"]:
                conflicts.append({"subject":subject,"value":value,"reason":"POLARITY_CONFLICT"})
                continue
        if value in sentence or normalize_fragment(sentence)==value:
            matches.append({"subject":subject,"value":value,"reason":"TEXT_MATCH"})
    status="CONFLICT" if conflicts else ("MATCH" if matches else "INSUFFICIENT")
    return {"status":status,"subject":canonical,"matches":matches,"conflicts":conflicts,
            "wiki_source":wiki.get("source") or wiki.get("url"),
            "wiki_truth_state":"EXTERNAL_UNVERIFIED",
            "memory_truth_state":"NOT_ASSESSED",
            "verified":False,"train_ready":False,"promoted":False}

def compare_store(wiki,path):
    return compare(wiki,load_propositions(Path(path)))
