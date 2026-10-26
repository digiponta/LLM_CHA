"""Single session-only router for preference, reason and agreement.

Keeps reported feelings separate from unverified external evidence. No persistence.
"""
from dataclasses import dataclass
from preference_dialogue_v09768 import PreferenceDialogue
from dialogue_agreement_v09771 import AgreementContext
from semantic_dialogue_state_v09770 import extract_preference, extract_reason

@dataclass(frozen=True)
class DialogueResult:
    reply: str
    route: str
    frame: object = None

class SemanticDialogueManager:
    def __init__(self):
        self.preference = PreferenceDialogue()
        self.agreement = AgreementContext()
        self.last_frame = None

    def handle(self, utterance, topic=None):
        text = str(utterance or "").strip()
        if not text or text.startswith("/"):
            return None
        agreement_reply = self.agreement.reply(text)
        if agreement_reply is not None:
            self.last_frame = None
            return DialogueResult(agreement_reply, "SEMANTIC_DIALOGUE_AGREEMENT")
        pending_topic = self.preference.awaiting_reason_for
        reply = self.preference.reply(text, topic)
        if reply is not None:
            frame = extract_preference(text) or extract_reason(text, pending_topic)
            self.last_frame = frame
            self.agreement.record(frame)
            return DialogueResult(reply, "TOPIC_PREFERENCE_ACK", frame)
        self.last_frame = None
        return None
