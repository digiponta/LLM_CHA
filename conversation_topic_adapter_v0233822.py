"""v0.2.33.82.2 conversation context adapter.

Call process_user_turn BEFORE the existing semantic / Truth Gate pipeline.
For READY, feed rewritten_query to that pipeline; never return it as a
user-visible fact or bypass the existing verification/generation path.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from multi_topic_context_v0233821 import MultiTopicContext

FOLLOWUPS = ("もう少し詳しく", "詳しく教えて", "もっと詳しく", "続き", "それについて")
RETURN_PATTERNS = ("の話に戻って", "について戻って")
TOPIC_SUFFIXES = ("について教えて", "とは何", "とは？", "とは?", "とは")
CONFIRM = "どの話題についてですか？"
UNKNOWN_TOPIC = "参照できる話題がありません。話題を指定してください。"

@dataclass(frozen=True)
class Route:
    action: str  # READY / CLARIFY / RESET / COMMAND / NO_TOPIC
    rewritten_query: Optional[str] = None
    topic: Optional[str] = None
    response: Optional[str] = None

class ConversationTopicAdapter:
    def __init__(self, context: Optional[MultiTopicContext] = None):
        self.context = context if context is not None else MultiTopicContext()

    @staticmethod
    def extract_topic(utterance: str) -> Optional[str]:
        text = utterance.strip().rstrip("。！？!? ")
        for suffix in TOPIC_SUFFIXES:
            if text.endswith(suffix):
                topic = text[:-len(suffix)].strip(" 「」")
                return topic or None
        return None

    def process_user_turn(self, utterance: str) -> Route:
        """Conservative deterministic routing; no semantic knowledge mutation."""
        text = utterance.strip()
        if text == "/reset":
            self.context.reset()
            return Route("RESET", response="会話の話題をリセットしました。")
        if text.startswith("/"):
            return Route("COMMAND")  # caller handles original command verbatim
        self.context.advance_turn()
        normalized = text.rstrip("。！？!? ")
        for phrase in RETURN_PATTERNS:
            if normalized.endswith(phrase):
                target = normalized[:-len(phrase)].strip(" 「」")
                if target and target in self.context.topics:
                    self.context.observe(target)
                    return Route("READY", rewritten_query=target + "について教えて", topic=target)
                return Route("NO_TOPIC", response=UNKNOWN_TOPIC)

        topic = self.extract_topic(text)
        if topic:
            admission = self.context.observe(topic)
            if admission.status != "RESOLVED":
                return Route("NO_TOPIC", response="話題の保持容量が不足しています。")
            return Route("READY", rewritten_query=text, topic=topic)

        if normalized in FOLLOWUPS:
            result = self.context.resolve(ambiguous_reference=
                normalized.startswith("それ"))
            if result.status == "AMBIGUOUS":
                return Route("CLARIFY", response=CONFIRM)
            if result.status != "RESOLVED":
                return Route("NO_TOPIC", response=UNKNOWN_TOPIC)
            return Route("READY",
                         rewritten_query=result.topic + "についてもう少し詳しく教えて",
                         topic=result.topic)

        return Route("READY", rewritten_query=text, topic=self.context.active_topic)
