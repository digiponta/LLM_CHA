"""v0.4.20 narrow conversation intent guard before retrieval.

Avoid keyword matching for fragments; never alter truth-state or memory.
"""
from __future__ import annotations
import re
import unicodedata
from persona_identity_guard_v0419 import identity_answer

FRAGMENTS=frozenset(("貴方は","あなたは","君は","きみは","私は","わたしは",
                     "貴方の","あなたの","君の","きみの","それは","これは",
                     "貴方って","あなたって"))
KNOWLEDGE=re.compile(r"^.{1,60}(?:とは|って何|とは何|について教えて)[？?。!！]*$")
CONVERSATION=re.compile(r"^(?:今日は何をしていたの|今日は何してたの|最近どう|元気ですか|元気\?|調子はどう)[？?。!！]*$")

def classify_dialogue_intent(query: str) -> dict:
    result={"version":"v0.4.20","intent":"OTHER","answer":None,
            "action":"PASS_THROUGH","truth_gate_modified":False,
            "semantic_memory_writes":0,"training_enabled":False}
    if not isinstance(query,str) or not query.strip() or len(query)>120:
        return result
    q=unicodedata.normalize("NFKC",query).strip().replace(" ","").replace("　","")
    if q.startswith("/") or "\n" in q or "\r" in q:
        return result
    if identity_answer(q) is not None:
        return dict(result,intent="IDENTITY",action="IDENTITY_ROUTE")
    # Only narrowly specified unfinished utterances. No general grammar guessing.
    if q in FRAGMENTS:
        return dict(result,intent="INCOMPLETE",answer="続きを聞かせて。",
                    action="ASK_CONTINUATION")
    if KNOWLEDGE.fullmatch(q):
        return dict(result,intent="KNOWLEDGE",action="PASS_THROUGH")
    if CONVERSATION.fullmatch(q):
        return dict(result,intent="CONVERSATION",action="PASS_THROUGH")
    return result
