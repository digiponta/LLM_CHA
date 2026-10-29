"""Resolve short taste replies from the most recent assistant question.

Only handles explicit, bounded conversational states. Knowledge questions
retain the normal LLM/Wikipedia path.
"""
import re

TASTE = re.compile(r"^(?:美味|おいしい|美味しい|うまい|旨い|最高|おいしかった|美味しかった|うまかった|甘い|酸っぱい|苦い|さっぱり|あっさり)(?:です|だった|だ|ね)?[！!。]*$")
QUESTION = re.compile(r"[？?]|(?:とは|の意味|の語源|について|教えて|説明して)")
class DialogueIntentGate:
    def __init__(self):
        self.awaiting_taste = False
    def observe_assistant(self, reply):
        self.awaiting_taste = bool(re.search(r"どんな味だった[？?]|味はどうだった[？?]",reply or ""))
    def respond(self,utterance):
        s=(utterance or "").strip()
        if QUESTION.search(s):
            self.awaiting_taste=False
            return None
        if self.awaiting_taste and TASTE.fullmatch(s):
            self.awaiting_taste=False
            return "おいしかったんだね。気に入ったようでよかった。" if re.match(r"美味|おいし|うま|旨|最高",s) else "その味が印象に残ったんだね。"
        self.awaiting_taste=False
        return None
