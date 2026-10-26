"""Atomic session-only Semantic Dialogue updates, with rollback on invalid state."""
import copy
from dataclasses import dataclass
from semantic_integrity_gate_v09782 import evaluate_integrity

@dataclass(frozen=True)
class TransactionResult:
    committed: bool
    dialogue_result: object
    status: str

def process_semantic_transaction(manager,topic_context,utterance):
    before_manager=copy.deepcopy(manager.__dict__)
    before_topic=getattr(topic_context,"active_topic",None)
    try:
        result=manager.handle(utterance,before_topic)
        if result is None:
            # A non-dialogue utterance may still expire clarification state.
            # Such updates are committed only if their resulting state is valid.
            pass
        elif result.next_topic is not None:
            topic_context.active_topic=result.next_topic
        decision=evaluate_integrity(manager,topic_context)
        if not decision.allow_dialogue:
            manager.__dict__.clear()
            manager.__dict__.update(before_manager)
            topic_context.active_topic=before_topic
            return TransactionResult(False,None,"ROLLBACK:"+decision.status)
        return TransactionResult(True,result,"COMMIT:"+decision.status)
    except Exception:
        manager.__dict__.clear()
        manager.__dict__.update(before_manager)
        topic_context.active_topic=before_topic
        return TransactionResult(False,None,"ROLLBACK:EXCEPTION")
