"""v0.2.33.82.9 isolated mixed-state end-to-end routing evaluator.

Uses the same topic adapter, cursor, and TruthOverlay classes as chat.py.
No checkpoint, corpus, review-store, or semantic-state changes.
"""
from __future__ import annotations
from dataclasses import dataclass
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
from grounded_expansion_v0233826 import PropositionCursor
from proposition_truth_v0233827 import TruthOverlay

@dataclass(frozen=True)
class Output:
    status: str
    proposition: str | None = None
    truth_state: str | None = None
    proposition_id: str | None = None

class MixedStateEvaluator:
    def __init__(self, corpus: dict[str, tuple[str,str,str]],
                 overlay: TruthOverlay):
        # corpus maps subject to (literal joined propositions, provenance,
        # inherited subject truth state). Fixture-only data.
        self.corpus = corpus
        self.overlay = overlay
        self.adapter = ConversationTopicAdapter()
        self.cursor = PropositionCursor()

    def turn(self, text: str) -> Output:
        route = self.adapter.process_user_turn(text)
        if route.action == "RESET":
            self.cursor.reset()
            return Output("RESET")
        if route.action != "READY":
            return Output(route.action)
        if route.topic is None or route.topic not in self.corpus:
            return Output("NO_TOPIC")
        subject = route.topic
        answer, provenance, subject_state = self.corpus[subject]
        # Fail closed for blocked subjects. This fixture uses the same blocked
        # categories as the existing subject Truth Gate.
        subject_allowed = subject_state not in ("FALSE","OUTDATED","CONTESTED")
        if not subject_allowed:
            return Output("BLOCK_SUBJECT", truth_state=subject_state)
        while True:
            proposition, _, _ = self.cursor.next(subject, answer)
            if proposition is None:
                return Output("EXHAUSTED")
            decision = self.overlay.decide(subject, proposition, provenance,
                                          subject_state, subject_allowed)
            if decision.allowed:
                return Output("DISPLAY", proposition, decision.state,
                              decision.proposition_id)
