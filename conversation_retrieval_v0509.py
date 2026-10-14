"""v0.5.9 explicit provenance-first retrieval of saved USER utterances.

Only speaker A/user is used. The source is a validated Conversation JSON.
This is not fact verification or model training. No generated AI answer is indexed.
"""
import json
from pathlib import Path
from conversation_resource_memory_v042866 import validate
from user_context_recovery_v0508 import UserContext

def retrieve(path,query,limit=3):
    if type(limit) is not int or not 1<=limit<=20:raise ValueError("invalid limit")
    p=Path(path)
    if not p.is_file() or p.is_symlink():raise ValueError("invalid conversation path")
    memory=json.loads(p.read_text(encoding="utf-8-sig"))
    validate(memory)
    wanted=UserContext();wanted.observe(query)
    continuation=wanted.continuation(query)
    user_turns=[t for t in memory["turns"] if t["speaker"] in ("A","user")]
    if continuation and not wanted.topic:
        # Recency recall without guessing the topic; still source-attributed.
        recent=[t for t in user_turns if UserContextTopic(t["text"])]
        eligible=recent
    else:
        eligible=[t for t in user_turns if wanted.topic and UserContextTopic(t["text"])==wanted.topic]
    rows=[]
    for t in reversed(eligible):
        context=UserContext();context.observe(t["text"])
        rows.append({"conversation_id":memory["conversation_id"],
          "turn_id":t["turn_id"],"speaker":"user","text":t["text"],
          "topic":context.topic,"subject":context.subject,
          "truth_state":"USER_REPORTED_UNVERIFIED","trusted_fact":False,
          "train_ready":False})
        if len(rows)>=limit:break
    return rows

def UserContextTopic(text):
    c=UserContext();c.observe(text)
    return c.topic

def restore_user_context(path,query):
    results=retrieve(path,query,limit=1)
    if not results:return None,[]
    c=UserContext();c.observe(results[0]["text"])
    return c,results
