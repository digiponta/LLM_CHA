"""Single session-only router for preference, reason and agreement.

Keeps reported feelings separate from unverified external evidence. No persistence.
"""
from dataclasses import dataclass
import re
from semantic_event_journal_v09774 import SemanticEventJournal
from clarification_reason_v09776 import parse_clarification
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
        self.journal = SemanticEventJournal()
        self.awaiting_clarification = None
        self.awaiting_new_reason = None

    def handle(self, utterance, topic=None):
        text = str(utterance or "").strip()
        if not text or text.startswith("/"):
            return None
        if self.awaiting_new_reason is not None:
            reason_topic = self.awaiting_new_reason
            new_reason = parse_clarification(text)
            self.awaiting_new_reason = None
            if new_reason is None:
                self.journal.record("clarification_cancelled", reason_topic)
            if new_reason is not None:
                self.journal.record("clarification_provided", reason_topic,
                                    updated_quality=new_reason)
                return DialogueResult(
                    f"{reason_topic}の{new_reason}が好きなんだね。",
                    "SEMANTIC_DIALOGUE_CLARIFICATION_PROVIDED")
        # Confirmation after a rejection acknowledges the correction request,
        # never reactivates the rejected preference.
        if self.awaiting_clarification is not None:
            clarification_topic = self.awaiting_clarification
            if re.fullmatch(r"(?:そうだよ|そうです|うん|はい|その通り)[。！! ]*", text):
                self.awaiting_clarification = None
                self.awaiting_new_reason = clarification_topic
                self.journal.record("clarification_acknowledged", clarification_topic)
                return DialogueResult(
                    "わかった。どんなところが好きなのか、もう少し教えて。",
                    "SEMANTIC_DIALOGUE_CLARIFICATION")
            new_reason = parse_clarification(text)
            self.awaiting_clarification = None
            if new_reason is None:
                self.journal.record("clarification_cancelled", clarification_topic)
            if new_reason is not None:
                self.journal.record("clarification_provided", clarification_topic,
                                    updated_quality=new_reason)
                return DialogueResult(
                    f"{clarification_topic}の{new_reason}が好きなんだね。",
                    "SEMANTIC_DIALOGUE_CLARIFICATION_PROVIDED")
        transition = parse_transition(text, topic, self.last_frame)
        if transition is not None:
            previous_quality = (self.last_frame.quality if self.last_frame is not None else None)
            self.journal.record(transition.intent, transition.topic,
                                previous_quality=None if transition.intent == "switch_topic" else previous_quality,
                                updated_quality=transition.quality,
                                source_topic=(topic or self.journal.replay().active_topic) if transition.intent == "switch_topic" else None,
                                target_topic=transition.topic if transition.intent == "switch_topic" else None)
            self.preference.awaiting_reason_for = None
            self.agreement.record(None)
            self.last_frame = None
            if transition.intent == "switch_topic":
                return DialogueResult(
                    f"{transition.topic}の話だね。何について知りたい？",
                    "SEMANTIC_DIALOGUE_TOPIC_SWITCH", next_topic=transition.topic)
            if transition.intent == "reject_previous":
                self.awaiting_clarification = transition.topic
                return DialogueResult("そうではなかったんだね。どういう意味だった？",
                                      "SEMANTIC_DIALOGUE_REJECTION")
            return DialogueResult(
                f"{transition.topic}は、きらきらより{transition.quality}が好きなんだね。",
                "SEMANTIC_DIALOGUE_CORRECTION")
        agreement_reply = self.agreement.reply(text)
        if agreement_reply is not None:
            self.journal.record("agreement", topic)
            self.last_frame = None
            return DialogueResult(agreement_reply, "SEMANTIC_DIALOGUE_AGREEMENT")
        pending_topic = self.preference.awaiting_reason_for
        reply = self.preference.reply(text, topic)
        if reply is not None:
            frame = extract_preference(text) or extract_reason(text, pending_topic)
            self.last_frame = frame
            if frame is not None:
                self.journal.record(frame.intent, frame.topic,
                                    updated_quality=frame.quality)
            self.agreement.record(frame)
            return DialogueResult(reply, "TOPIC_PREFERENCE_ACK", frame)
        self.last_frame = None
        self.preference.awaiting_reason_for = None
        return None
