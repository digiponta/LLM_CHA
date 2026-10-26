"""Session-only, topic-aware preference dialogue; no memory writes."""
import re
from topic_preference_ack_v09767 import PREFERENCE

REASON = re.compile(r"^(?:(?:だって|理由は)[、, ]*)?(?P<reason>きれい|綺麗|美しい|輝きが好き|虹色の輝きが好き|ファイアが好き)(?:だから|なんです|です|だ|ね|よ)?[。！! ]*$")

class PreferenceDialogue:
    def __init__(self):
        self.awaiting_reason_for = None

    def reply(self, utterance, topic=None):
        text = str(utterance or "").strip()
        if not text or text.startswith("/"):
            return None
        m = PREFERENCE.fullmatch(text)
        if m:
            subject = m.group("subject").strip("、, ")
            if not subject:
                return None
            self.awaiting_reason_for = subject
            return f"{subject}が好きなんだね。どんなところが気に入っている？"
        if self.awaiting_reason_for and (m := REASON.fullmatch(text)):
            subject = self.awaiting_reason_for
            self.awaiting_reason_for = None
            reason = m.group("reason")
            return f"{subject}の{reason}が気に入っているんだね。" if reason in ("輝きが好き","虹色の輝きが好き","ファイアが好き") else f"{subject}が{reason}なんだね。"
        # Do not carry preference follow-up across unrelated turns.
        self.awaiting_reason_for = None
        return None
