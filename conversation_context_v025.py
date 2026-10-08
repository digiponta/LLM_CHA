"""v0.2.5 separate transient user conversation context from trusted replies.

Only user-supplied messages are retained as context; rejected assistant candidates
are never recycled into prompts, learning samples, or verified knowledge.
"""
from __future__ import annotations
import re
from collections import deque

class ConversationContext:
    def __init__(self, limit=12):
        self.messages = deque(maxlen=limit)
    def clear(self):
        self.messages.clear()
    def add_user(self, text):
        self.messages.append({"text": text.strip(), "answered": False})
    def mark_answered(self):
        if self.messages:
            self.messages[-1]["answered"] = True
    def pending_prefix(self, *, current, max_pending=2):
        # Current input is the last entry. Include only previous short,
        # unacknowledged user utterances to keep AI/user turn structure intact.
        previous = list(self.messages)[:-1]
        pending = []
        for entry in reversed(previous):
            if entry["answered"]:
                break
            message = entry["text"]
            if len(message) > 80 or "\n" in message or re.search(r"(とは|理由|なぜ|説明して|\?)", message):
                break
            pending.append(message)
            if len(pending) >= max_pending:
                break
        pending.reverse()
        if not pending:
            return current
        # Fold adjacent user turns into one user turn; no invented AI reply.
        return "。".join(pending + [current])
