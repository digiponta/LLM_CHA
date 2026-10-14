#!/usr/bin/env python3
"""LLM_CHA v0.4.28.57 — Conversational Semantic Memory (experimental).

Conversation-local structured state, source-preserving, no embeddings invented,
no model training and no automatic promotion into long-term memory.
"""
import argparse
import json
import re
from pathlib import Path

VERSION = "v0.4.28.57"
TERMS = ("車","駐車場","東京","地方","旅行","長野","新潟","映画","文房具",
         "猫","カレー","仕事","学校","趣味","音楽","本","天気","家族")
NEGATIONS = ("持っていない","持ってません","持ってない")
ROLE_MAP = {"user":"user","assistant":"assistant","人":"user","相手":"assistant"}

def new_memory(conversation_id):
    if not isinstance(conversation_id,str) or not conversation_id.strip():
        raise ValueError("conversation_id required")
    return {"version":VERSION,"conversation_id":conversation_id,"last_turn":0,
            "keywords":[],"current_topic":None,"propositions":[],
            "recent_turns":[],"pending_review":[],"promotion_status":"not_promoted",
            "train_ready":False}

def keyword_candidates(text):
    # Explicit, inspectable baseline; low recall is expected.
    return [term for term in TERMS if term in text]

def update(memory, role, text, *, turn_id=None, recent_limit=5):
    if role not in ROLE_MAP or not isinstance(text,str) or not text.strip():
        raise ValueError("recognized role and nonempty text required")
    if recent_limit<1:raise ValueError("recent_limit must be positive")
    last=memory.get("last_turn")
    if not isinstance(last,int) or last<0:raise ValueError("invalid state")
    if turn_id is None:turn_id=last+1
    if not isinstance(turn_id,int) or isinstance(turn_id,bool) or turn_id!=last+1:
        raise ValueError("turn_id must be sequential")
    role=ROLE_MAP[role]
    utterance=text.strip()
    memory["last_turn"]=turn_id
    hits=keyword_candidates(utterance)
    for word in hits:
        if word not in memory["keywords"]:memory["keywords"].append(word)
    if hits:memory["current_topic"]=hits[0]
    memory["recent_turns"].append({"turn_id":turn_id,"role":role,"text":utterance})
    memory["recent_turns"]=memory["recent_turns"][-recent_limit:]
    # Very narrow explicit extractors; avoid treating arbitrary keywords as facts.
    if role=="user" and "車" in utterance and any(x in utterance for x in NEGATIONS):
        proposition={"subject":"user","predicate":"owns","object":"car",
                     "polarity":False,"truth_state":"USER_REPORTED_UNVERIFIED",
                     "source_turn":turn_id,"source_text":utterance,
                     "status":"candidate"}
        # Keep revisions and sources; do not silently overwrite earlier facts.
        memory["propositions"].append(proposition)
        memory["pending_review"].append({"source_turn":turn_id,"reason":"candidate_personal_fact"})
    memory["train_ready"]=False
    return memory

def build_prompt_context(memory,max_keywords=8,recent_limit=3):
    if max_keywords<0 or recent_limit<0:raise ValueError("limits must be nonnegative")
    keywords=memory["keywords"][-max_keywords:] if max_keywords else []
    propositions=memory["propositions"][-5:]
    return {"topic":memory["current_topic"],"keywords":keywords,
            "unverified_propositions":[{
                "subject":p["subject"],"predicate":p["predicate"],
                "object":p["object"],"polarity":p["polarity"],
                "source_turn":p["source_turn"],"truth_state":p["truth_state"]}
                for p in propositions],
            "recent_turns":memory["recent_turns"][-recent_limit:] if recent_limit else [],
            "context_is_authoritative":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True,help='JSON file: {"conversation_id":"...","turns":[{"role":"user","text":"..."}]}')
    p.add_argument("--output",default="results/conversation_semantic_memory_v042857.json")
    p.add_argument("--recent-limit",type=int,default=5)
    a=p.parse_args()
    source=Path(a.input);dest=Path(a.output)
    if source.resolve()==dest.resolve():raise ValueError("input and output must differ")
    data=json.loads(source.read_text(encoding="utf-8"))
    memory=new_memory(data["conversation_id"])
    for turn in data["turns"]:
        update(memory,turn["role"],turn["text"],turn_id=turn.get("turn_id"),
               recent_limit=a.recent_limit)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(memory,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"version":VERSION,"turns":memory["last_turn"],
          "keywords":len(memory["keywords"]),"propositions":len(memory["propositions"]),
          "train_ready":False,"runtime_modified":False},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
