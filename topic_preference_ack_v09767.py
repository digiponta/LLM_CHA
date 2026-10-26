"""Conservative topic-aware preference acknowledgement, no factual claims.

Responses here are ephemeral dialogue, not learned preferences or approved facts.
"""
import re

PREFERENCE = re.compile(
    r"^(?:私は[、, ]*|僕は[、, ]*|わたしは[、, ]*)?"
    r"(?P<subject>[^。！？!?\n]{2,50}?)"
    r"(?:が|は)(?P<adv>とても|すごく|かなり|大好きなほど|)?"
    r"(?P<sentiment>大好き|好き)(?:です|だ|なんです|なの)?[。！! ]*$"
)

def acknowledge(text, active_topic=None):
    q = str(text or "").strip()
    if not q or q.startswith("/"):
        return None
    match = PREFERENCE.fullmatch(q)
    if match is None:
        return None
    subject = match.group("subject").strip("、, ")
    if not subject or len(subject) > 50:
        return None
    # Handle user-centered literal statement only, without guessing feelings
    # or creating persistent personal information.
    sentiment = match.group("sentiment")
    if active_topic and subject == active_topic:
        return f"{subject}が{sentiment}なんだね。どんなところが気に入っている？"
    return f"{subject}が{sentiment}なんだね。どんなところが気に入っている？"
