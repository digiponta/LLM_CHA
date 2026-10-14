#!/usr/bin/env python3
"""LLM_CHA v0.4.28.58: evidence-bound conversational semantic extraction.

Conservative Japanese rule patterns. Candidate statements are not verified facts.
Does not change model checkpoints, chat.py, or long-term memory.
"""
import re
from copy import deepcopy
from conversation_semantic_memory_v042857 import new_memory, update

VERSION="v0.4.28.58"
# Ordered explicit rules. A match must include the actual user statement.
RULES=[
 ("owns","car",False,re.compile(r"(?:私|僕|わたし|自分)(?:は|も)?[^。\n]{0,35}?車(?:を|は)?持って(?:いない|ない|ません)")),
 ("owns","car",True,re.compile(r"(?:私|僕|わたし|自分)(?:は|も)?[^。\n]{0,35}?車(?:を|は)?持って(?:いる|ます|る)")),
 ("likes","movie",True,re.compile(r"(?:私|僕|わたし|自分)(?:は|も)?[^。\n]{0,25}?映画(?:が|は)?好き")),
 ("likes","movie",False,re.compile(r"(?:私|僕|わたし|自分)(?:は|も)?[^。\n]{0,25}?映画(?:が|は)?好き(?:ではない|じゃない)")),
]
# Prevent specific negative patterns from being mistakenly matched as positives.
NEGATIVE_LIKES=re.compile(r"映画(?:が|は)?好き(?:ではない|じゃない)")

def extract_candidates(text, role, turn_id):
    if role not in ("user","人"):
        return []
    matches=[]
    for predicate,obj,polarity,pattern in RULES:
        for match in pattern.finditer(text):
            if predicate=="likes" and polarity and NEGATIVE_LIKES.search(text[match.start():match.end()+8]):
                continue
            matches.append({
                "subject":"user","predicate":predicate,"object":obj,
                "polarity":polarity,"truth_state":"USER_REPORTED_UNVERIFIED",
                "source_turn":turn_id,"source_span":[match.start(),match.end()],
                "source_text":text,"status":"candidate","extractor":VERSION})
    # Explicit overlapping matches are not double-counted.
    unique={}
    for m in matches:
        key=(m["predicate"],m["object"],m["polarity"],tuple(m["source_span"]))
        unique[key]=m
    return list(unique.values())

def apply_turn(memory,role,text,*,turn_id=None,recent_limit=5):
    # Validate/update on a copy to avoid partially mutated state on failure.
    staged=deepcopy(memory)
    before=staged["last_turn"]
    update(staged,role,text,turn_id=turn_id,recent_limit=recent_limit)
    n=staged["last_turn"]
    # Replace earlier narrow extractor candidates from this turn to avoid double-count.
    staged["propositions"]=[p for p in staged["propositions"] if p["source_turn"]!=n]
    staged["pending_review"]=[p for p in staged["pending_review"] if p["source_turn"]!=n]
    found=extract_candidates(text,role,n)
    staged["propositions"].extend(found)
    staged["pending_review"].extend(
        {"source_turn":n,"reason":"unverified_semantic_candidate",
         "predicate":p["predicate"],"object":p["object"]} for p in found)
    staged["extractor_version"]=VERSION
    staged["train_ready"]=False
    memory.clear()
    memory.update(staged)
    return found

def build_from_turns(conversation_id,turns,recent_limit=5):
    memory=new_memory(conversation_id)
    for turn in turns:
        apply_turn(memory,turn["role"],turn["text"],
                   turn_id=turn.get("turn_id"),recent_limit=recent_limit)
    return memory
