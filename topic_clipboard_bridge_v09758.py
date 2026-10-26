"""Resolve topic-keyed questions against temporary clipboard evidence.

Returns no answer when the source does not support the question.
Never promotes source content to approved knowledge or model training.
"""
from clipboard_evidence_binding_v09757 import ClipboardEvidenceSession


def answer_from_topic_clipboard(question, topic, copied_text):
    if not topic or not copied_text:
        return None
    session = ClipboardEvidenceSession()
    session.ingest(copied_text, subject=topic)
    result = session.answer(question, resolved_subject=topic)
    return result.render() if result is not None else None
