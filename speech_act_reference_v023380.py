"""v0.2.33.80 conservative speech-act and ambiguous-reference routing.

No fact promotion and no implicit truth-state changes.
"""
import re
from multi_intent_reference_v023375 import clarify_reference

THANKS = re.compile(r"^(?:どうも)?(?:ありがとう(?:ございます)?|助かりました|助かった)(?:[。！!]+)?$")
FOLLOWUP = re.compile(r"^(?:もう少し詳しく|もう少し詳しく教えて|詳しく教えて)(?:ください)?[。！？!?]?$")
AMBIGUOUS = re.compile(r"^(?:あの実験の続き|あの実験(?:について)?|先ほどの実験の続き|その実験の続き)(?:[。！？!?])?$")

TOPIC_QUERY = re.compile(
    r"^([\\w一-龥ぁ-んァ-ヶー]{1,32})(?:とは|について教えて|について説明して)(?:ください)?[。！？!?]?$"
)

def extract_topic(user_text):
    match = TOPIC_QUERY.fullmatch(user_text.strip())
    return match.group(1) if match else None

def route_speech_act(user_text, previous_user=None):
    text=user_text.strip()
    if not text or text.startswith("/"):
        return None
    if THANKS.fullmatch(text):
        return {"kind":"ACKNOWLEDGEMENT","answer":"どういたしまして。"}
    if AMBIGUOUS.fullmatch(text):
        return {"kind":"REFERENCE_CLARIFY","answer":clarify_reference()}
    if FOLLOWUP.fullmatch(text):
        topic = previous_user
        if topic:
            # Always re-enter the existing Truth Gate, never answer from
            # the conversational context directly.
            return {"kind":"FOLLOWUP_TOPIC_ROUTE",
                    "topic":topic,"routed_query":topic+"とは"}
        return {"kind":"FOLLOWUP_CLARIFY",
                "answer":"どの話題について詳しく知りたいですか？対象を教えてください。"}
    return None
