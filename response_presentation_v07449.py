"""v0.7.44.9: conservative presentation-only response length selection.

Never edits source evidence. This is a presentation transform, not a truth gate.
"""
import re

def is_bare_term(text):
    value=(text or "").strip()
    return bool(value and len(value)<=24 and not re.search(r"[\s。！？?、]",value)
                and not any(x in value for x in ("とは","って何","について","教えて","説明")))

def present_synonym_recovery(user_text, recovered_term, evidence_answer):
    if not is_bare_term(user_text):
        return evidence_answer
    if not recovered_term:
        return evidence_answer
    return f"「{user_text.strip()}」は「{recovered_term}」の別の呼び方。詳しく説明する？"
