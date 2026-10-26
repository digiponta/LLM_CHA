"""Single session-only router for preference, reason and agreement.

Keeps reported feelings separate from unverified external evidence. No persistence.
"""
from dataclasses import dataclass
from semantic_dialogue_transition_v09773 import parse_transition
from preference_dialogue_v09768 import PreferenceDialogue
from dialogue_agreement_v09771 import AgreementContext
from semantic_dialogue_state_v09770 import extract_preference, extract_reason

@dataclass(frozen=True)
class DialogueResult:
    reply: str
    route: str
    frame: object = None
    next_topic: str | None = None

class SemanticDialogueManager:
    def __init__(self):
        self.preference = PreferenceDialogue()
        self.agreement = AgreementContext()
        self.last_frame = None

    def handle(self, utterance, topic=None):
        text = str(utterance or "").strip()
        if not text or text.startswith("/"):
            return None
        transition = parse_transition(text, topic, self.last_frame)
        if transition is not None:
            self.preference.awaiting_reason_for = None
            self.agreement.record(None)
            self.last_frame = None
            if transition.intent == "switch_topic":
                return DialogueResult(
                    f"{transition.topic}の話だね。何について知りたい？",
                    "SEMANTIC_DIALOGUE_TOPIC_SWITCH", next_topic=transition.topic)
            if transition.intent == "reject_previous":
                return DialogueResult("そうではなかったんだね。どういう意味だった？",
                                      "SEMANTIC_DIALOGUE_REJECTION")
            return DialogueResult(
                f"{transition.topic}は、きらきらより{transition.quality}が好きなんだね。",
                "SEMANTIC_DIALOGUE_CORRECTION")
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
