"""v0.2.33.74: narrow, evidence-independent quality guard for greetings.

Do not apply this guard to requests for facts, persona identity, reference
resolution, training or the Truth-Aware knowledge paths.
"""
import re

GREETINGS={
    "こんにちは":"こんにちは。",
    "こんばんは":"こんばんは。",
    "おはよう":"おはようございます。",
    "おはようございます":"おはようございます。",
    "やあ":"こんにちは。",
}
def greeting_repair(user_text, candidate, accepted):
    """Return (reply_or_none, reason).

    Exact whole-turn matching is intentional: do not incorrectly treat
    'こんにちは、宇宙について教えて' as a safe greeting-only query.
    """
    text=re.sub(r"[\s　]+","",user_text or "")
    text=re.sub(r"[。！!？?]+$","",text)
    fallback=GREETINGS.get(text)
    if fallback is None:
        return None,"not_greeting_only"
    clean=(candidate or "").strip()
    if (not accepted or not clean or len(clean)>32 or
        not re.search(r"^(?:こんにちは|こんばんは|おはよう|やあ)",clean) or
        re.search(r"未学習|分からない|理解できない",clean)):
        return fallback,"greeting_quality_fallback"
    return None,"generation_preserved"
