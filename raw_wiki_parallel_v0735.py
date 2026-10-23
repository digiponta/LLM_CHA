"""Compose unverified raw/corpus source evidence beside Wikipedia search evidence.

Return original answer on unavailable, invalid or ambiguous Wikipedia results.
This operation does not validate either source or change the memory lifecycle.
"""
from experimental_wiki_append_v0734 import append_wikipedia

def parallel_evidence(raw_answer,concept,lookup):
    if not isinstance(raw_answer,str) or not raw_answer.strip():
        return {"answer":raw_answer,"wiki_status":"SKIPPED"}
    response=append_wikipedia(raw_answer,concept,lookup=lookup)
    return response
