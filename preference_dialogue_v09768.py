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
            return f"{subject}の{reason[:-2]}が好きなんだね。" if reason.endswith("が好き") else f"{subject}が{reason}なんだね。"
        if self.awaiting_reason_for:
            # Accept a bounded sensory reason, without making a factual claim
            # about the object or memorizing a personal preference.
            sensory = re.fullmatch(
                r"(?P<quality>きらきら(?:して(?:い)?る)?|キラキラ(?:して(?:い)?る)?|"
                r"輝いて(?:い)?る|色がきれい|綺麗|きれい|美しい)"
                r"(?:ところ|感じ|様子)?(?:が|は)"
                r"(?P<feeling>心地よい|好き|素敵|いい|落ち着く)"
                r"(?:です|んです|よ|ね)?[。！! ]*",
                text)
            if sensory:
                subject = self.awaiting_reason_for
                self.awaiting_reason_for = None
                return (f"{subject}の{sensory.group('quality')}ところが"
                        f"{sensory.group('feeling')}んだね。")
        # Do not carry preference follow-up across unrelated turns.
        self.awaiting_reason_for = None
        return None
