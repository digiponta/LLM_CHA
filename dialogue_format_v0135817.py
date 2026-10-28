"""Canonical one-turn dialogue format for BOTH training and inference.

Keep legacy newline/spacing normalization explicit; do not silently change
the behavior of arbitrary multi-turn or prose input.
"""
import re

PROMPT_PREFIX="人: "
ANSWER_SEPARATOR="\nAI: "

def prompt_for(user):
    if not isinstance(user,str) or not user.strip():
        raise ValueError("non-empty user text required")
    return PROMPT_PREFIX+user.strip()+ANSWER_SEPARATOR

def dialogue_for(user,answer):
    if not isinstance(answer,str) or not answer.strip():
        raise ValueError("non-empty assistant text required")
    return prompt_for(user)+answer.strip()

def split_dialogue(record):
    if not isinstance(record,str) or not record.startswith(PROMPT_PREFIX):
        raise ValueError("not a canonical dialogue")
    if record.count(ANSWER_SEPARATOR)!=1:
        raise ValueError("expected exactly one AI delimiter")
    user,answer=record.split(ANSWER_SEPARATOR,1)
    if not user[len(PROMPT_PREFIX):].strip() or not answer.strip():
        raise ValueError("empty user/answer")
    return user+ANSWER_SEPARATOR,answer

def canonicalize_legacy(record):
    """Convert only unambiguous single-line historic '人: ... AI: ...' records."""
    if not isinstance(record,str):
        raise ValueError("dialogue must be str")
    if record.startswith(PROMPT_PREFIX) and record.count(ANSWER_SEPARATOR)==1:
        prefix,answer=split_dialogue(record)
        return prefix+answer
    if "\n" in record or record.count(" AI: ")!=1 or not record.startswith(PROMPT_PREFIX):
        raise ValueError("ambiguous legacy dialogue")
    left,right=record.split(" AI: ",1)
    return dialogue_for(left[len(PROMPT_PREFIX):],right)

def check_prompt(record,prompt):
    expected=split_dialogue(record)[0]
    return prompt==expected
