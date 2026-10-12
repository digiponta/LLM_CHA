"""LLM_CHA v0.2.33.82.1: transient multi-topic conversation context.

This module contains no semantic-store writes, training, or Truth Gate bypass.
The calling runtime must validate any selected topic against its existing
knowledge/truth pipeline before producing an answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Topic:
    name: str
    last_turn: int
    first_turn: int


@dataclass(frozen=True)
class Resolution:
    status: str  # RESOLVED, AMBIGUOUS, MISSING, RESET
    topic: Optional[str] = None
    candidates: tuple[str, ...] = ()


class MultiTopicContext:
    """Bounded conversation-only topic history; no persistent knowledge state."""

    def __init__(self, max_topics: int = 8, ttl_turns: int = 12):
        if max_topics < 1 or ttl_turns < 1:
            raise ValueError("max_topics and ttl_turns must be positive")
        self.max_topics = max_topics
        self.ttl_turns = ttl_turns
        self.turn = 0
        self._topics: dict[str, Topic] = {}
        self.active_topic: Optional[str] = None

    @property
    def topics(self) -> tuple[str, ...]:
        self._expire()
        return tuple(sorted(self._topics, key=lambda k: (-self._topics[k].last_turn, k)))

    def _expire(self) -> None:
        expired = [k for k, t in self._topics.items()
                   if self.turn - t.last_turn > self.ttl_turns]
        for k in expired:
            del self._topics[k]
        if self.active_topic not in self._topics:
            self.active_topic = None

    def advance_turn(self) -> None:
        self.turn += 1
        self._expire()

    def observe(self, topic: str) -> Resolution:
        """Register an explicitly extracted topic, not a fact or truth assertion."""
        topic = topic.strip()
        if not topic or topic.startswith("/"):
            return Resolution("MISSING")
        self._expire()
        if topic in self._topics:
            self._topics[topic].last_turn = self.turn
        else:
            if len(self._topics) >= self.max_topics:
                oldest = min(self._topics, key=lambda k: (
                    self._topics[k].last_turn, self._topics[k].first_turn, k))
                del self._topics[oldest]
            self._topics[topic] = Topic(topic, self.turn, self.turn)
        self.active_topic = topic
        return Resolution("RESOLVED", topic)

    def resolve(self, explicit_topic: Optional[str] = None,
                ambiguous_reference: bool = False) -> Resolution:
        """Fail closed on ambiguous references; never guess across topics."""
        self._expire()
        if explicit_topic:
            name = explicit_topic.strip()
            if name in self._topics:
                return Resolution("RESOLVED", name)
            return Resolution("MISSING")
        if not self._topics:
            return Resolution("MISSING")
        if ambiguous_reference and len(self._topics) > 1:
            return Resolution("AMBIGUOUS", candidates=self.topics)
        if self.active_topic is not None:
            return Resolution("RESOLVED", self.active_topic)
        return Resolution("MISSING")

    def reset(self) -> Resolution:
        self._topics.clear()
        self.active_topic = None
        return Resolution("RESET")

    def handle_command(self, text: str) -> Optional[Resolution]:
        """Only exact /reset is handled; unrelated slash commands pass through."""
        if text.strip() == "/reset":
            return self.reset()
        return None

    def snapshot(self) -> dict:
        """Diagnostic snapshot, not a serialized knowledge-memory artifact."""
        self._expire()
        return {"turn": self.turn, "active_topic": self.active_topic,
                "topics": list(self.topics)}
