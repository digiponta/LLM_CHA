"""LLM_CHA v0.2.33.82.3 — conservative multi-topic runtime bridge.

This is an opt-in integration shell; it DOES NOT replace chat.py's
Truth Gate or semantic retrieval. A verified response function is mandatory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter


@dataclass(frozen=True)
class RuntimeResult:
    status: str
    text: str
    topic: Optional[str] = None
    routed_query: Optional[str] = None


class MultiTopicChatRuntime:
    """Dispatch topic-resolved queries to an injected, truth-aware responder.

    `verified_responder(query)` MUST invoke the existing Semantic Memory,
    Truth Gate and LLM response process. This wrapper cannot validate that
    contract and must never supply a standalone unconstrained generator.
    """

    def __init__(self, verified_responder: Callable[[str], str],
                 command_handler: Optional[Callable[[str], str]] = None,
                 adapter: Optional[ConversationTopicAdapter] = None):
        if not callable(verified_responder):
            raise ValueError("verified_responder is required")
        self.verified_responder = verified_responder
        self.command_handler = command_handler
        self.adapter = adapter if adapter is not None else ConversationTopicAdapter()

    def respond(self, user_input: str) -> RuntimeResult:
        route = self.adapter.process_user_turn(user_input)
        if route.action in ("RESET", "CLARIFY", "NO_TOPIC"):
            return RuntimeResult(route.action, route.response or "", route.topic)
        if route.action == "COMMAND":
            if self.command_handler is None:
                return RuntimeResult("COMMAND_UNHANDLED", "このコマンドは処理できません。")
            try:
                output = self.command_handler(user_input)
            except Exception:
                return RuntimeResult("ERROR", "コマンド処理に失敗しました。")
            return RuntimeResult("COMMAND", str(output))
        if route.action != "READY" or route.rewritten_query is None:
            return RuntimeResult("ERROR", "文脈の解決に失敗しました。")
        try:
            output = self.verified_responder(route.rewritten_query)
            if not isinstance(output, str):
                raise TypeError("verified responder must return a string")
        except Exception:
            return RuntimeResult("ERROR", "検証済み応答処理に失敗しました。",
                                 route.topic, route.rewritten_query)
        return RuntimeResult("ANSWER", output, route.topic, route.rewritten_query)


def interactive_main() -> None:
    """No demo responder: fail closed until the real Truth Gate is wired."""
    print("LLM_CHA v0.2.33.82.3: verified responder not configured.")
    print("Integrate MultiTopicChatRuntime into your existing Truth Gate runtime.")
    raise SystemExit(2)


if __name__ == "__main__":
    interactive_main()
