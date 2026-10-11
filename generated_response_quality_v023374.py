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
    # Standalone greetings have a strict allowlist. Greeting-prefixed
    # hallucinations (even if accepted by the LM gate) must not pass.
    allowed = {
        "こんにちは": {"こんにちは。", "こんにちは！", "こんにちは"},
        "こんばんは": {"こんばんは。", "こんばんは！", "こんばんは"},
        "おはよう": {"おはようございます。", "おはよう。", "おはようございます"},
        "おはようございます": {"おはようございます。", "おはようございます"},
        "やあ": {"やあ。", "やあ", "こんにちは。"},
    }[text]
    if accepted and clean in allowed:
        return None,"generation_preserved"
    return fallback,"greeting_quality_fallback"
