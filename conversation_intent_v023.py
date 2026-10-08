"""LLM_CHA v0.2.3: narrowly scoped persona and conversational context routing.

Never use this router for factual knowledge questions. Character profile identity is
presentation metadata, not asserted evidence about the model checkpoint.
"""
from __future__ import annotations
import re
from character_profile_v010 import CharacterProfile

IDENTITY = (
    re.compile(r"^(?:お?名前を(?:伺えますか|教えて(?:ください)?|聞かせて)|あなた(?:の名前は|は誰(?:ですか)?|って誰)|自分が何者か説明して|自己紹介(?:してください|して)?)\s*[？?。]?$"),
)
THANKS = re.compile(r"^(?:ありがとう(?:ございます)?|助かりました|感謝します)\s*[！!。]?$")
TIRED = re.compile(r"(?:疲れ|くたくた|しんどい)")
INVITE = re.compile(r"(?:おしゃべり|雑談|話しませんか|話さない)")
BOOK_FOLLOWUP = re.compile(r"^(?:その本(?:は|って)|それ(?:は|って))")

def intent_reply(text: str, profile: CharacterProfile | None, history: list[tuple[str,str]]):
    q = text.strip()
    if not profile:
        return None
    if any(pattern.fullmatch(q) for pattern in IDENTITY):
        return ("identity", f"{profile.display_name}。")
    if THANKS.fullmatch(q):
        return ("acknowledgement", "どういたしまして。")
    if TIRED.search(q) and len(q) <= 50 and not ("原因" in q or "理由" in q):
        return ("feeling", "そう。無理せず少し休むといい。")
    if INVITE.search(q) and len(q) <= 40:
        return ("casual", "ええ。何について話す？")
    # Context answer is only for informal follow-ups to a previously
    # accepted conversational turn; it never invents facts about the book.
    if BOOK_FOLLOWUP.search(q) and history:
        prior = history[-1][0]
        if "本" in prior or "小説" in prior or "読書" in prior:
            return ("book_context", "どんなところが印象に残った？")
    return None
