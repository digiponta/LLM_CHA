"""v0.6.17: session-local self-identity follow-up resolution."""
import re

class IdentityContext:
    def __init__(self):
        self.pending=False

    def respond(self, utterance):
        t=utterance.strip()
        if not t or t.startswith("/"):
            return None
        if re.fullmatch(r"(貴方|あなた|君|きみ)(?:は|って|とは)?[？?]?",t):
            self.pending=True
            return ("私について、何を知りたい？ 名前や好きなことなら答えられる。",
                    "IDENTITY_CLARIFY")
        if re.fullmatch(r"(?:貴方|あなた|君|きみ)の名前は?[？?]?",t):
            self.pending=False
            return ("長門有希。","IDENTITY_DIRECT")
        if self.pending and re.fullmatch(r"(?:名前は?|お名前は?)[？?]?",t):
            self.pending=False
            return ("長門有希。","IDENTITY_FOLLOWUP")
        if self.pending and re.fullmatch(r"(?:好きなこと|趣味)(?:は|って)?[？?]?",t):
            self.pending=False
            return ("読書が好き。静かな環境を好む。","IDENTITY_FOLLOWUP")
        # An unrelated utterance invalidates the pending clarification.
        self.pending=False
        return None
