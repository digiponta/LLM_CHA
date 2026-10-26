"""Handle short agreement as an ephemeral follow-up to a preference dialogue."""
import re

_AGREEMENT = re.compile(r"^(?:そうだよ|そうです|そうだね|そうですね|うん|はい|その通り|まさにそう)(?:ね|よ)?[。！! ]*$")

class AgreementContext:
    def __init__(self):
        self.topic = None
        self.expected = False
    def record(self, frame):
        self.expected = bool(frame is not None and frame.intent == "explain_preference")
        self.topic = frame.topic if self.expected else None
    def reply(self, utterance):
        text = str(utterance or "").strip()
        if self.expected and _AGREEMENT.fullmatch(text):
            topic = self.topic
            self.expected, self.topic = False, None
            return f"うん。{topic}の魅力が伝わってくるね。"
        self.expected, self.topic = False, None
        return None
