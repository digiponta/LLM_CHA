"""v0.2.9 dialogue-state and repeated-question detection.

A conservative, inspectable heuristic. Never promotes knowledge or writes memory.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher

def normalize(s: str) -> str:
    return re.sub(r"[\s。？！?!、,.]+", "", s or "").strip()

def dialogue_state(history: list[tuple[str,str]], current: str) -> dict:
    if not history:
        return {"has_previous":False,"previous_question":"","user_answered":False}
    prior_user, prior_ai = history[-1]
    previous_question = prior_ai.strip() if ("？" in prior_ai or "?" in prior_ai) else ""
    # A brief follow-up after a question often answers it.
    user_answered = bool(previous_question and current.strip() and len(current.strip())<=35
                         and not re.search(r"[？?]",current))
    return {"has_previous":True,"previous_question":previous_question,
            "user_answered":user_answered}

def repeat_check(current: str, proposed: str, history: list[tuple[str,str]], threshold=0.76):
    if not history:return False,0.0
    previous=history[-1][1]
    left,right=normalize(previous),normalize(proposed)
    similarity=SequenceMatcher(None,left,right).ratio() if left and right else 0.0
    state=dialogue_state(history,current)
    # Restrict to a probable answer to the immediately preceding AI question;
    # do not reject normal acknowledgments of entirely separate intents.
    is_repeat=bool(state["user_answered"] and similarity>=threshold and len(right)>=8)
    return is_repeat,similarity
