"""v0.2.34.3 explicit, opt-in context recovery bridge.

Save only topic names and IDs of already presented propositions.
Every load passes through the current corpus and current subject Truth Gate.
No automatic persistence, no truth writes, no model updates.
"""
from __future__ import annotations
from pathlib import Path
import os
import tempfile
from longterm_context_v02340 import ContextCheckpoint
from corpus_restore_adapter_v023342 import restore_from_corpus
from proposition_truth_v0233827 import TruthOverlay, proposition_id
from retrieval_first_runtime_v1012161 import resolve_subject

def capture(topic_context, proposition_cursor, corpus_path) -> str:
    checkpoint=ContextCheckpoint()
    live=set(topic_context.topics)
    for subject in live:
        hit=resolve_subject(corpus_path,subject)
        if not hit.hit:
            continue
        for statement in hit.answer.split(" / "):
            statement=statement.strip()
            if statement and statement in proposition_cursor.seen.get(subject,set()):
                checkpoint.remember(subject,proposition_id(subject,statement,hit.provenance))
    if topic_context.active_topic in checkpoint.topics:
        checkpoint.switch(topic_context.active_topic)
    else:
        checkpoint.active_topic=None
    return checkpoint.export()

def save(path, topic_context, proposition_cursor, corpus_path):
    data=capture(topic_context,proposition_cursor,corpus_path)
    output=Path(path)
    if not output.parent.is_dir():
        raise FileNotFoundError(output.parent)
    fd, pending = tempfile.mkstemp(prefix=".llm-cha-context-", suffix=".tmp", dir=str(output.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(pending, output)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)
    return len(ContextCheckpoint.restore(data).topics)

def load(path, topic_adapter, proposition_cursor, corpus_path, subject_gate, overlay:TruthOverlay):
    # Read and validate before mutating live session.
    source=Path(path)
    if source.stat().st_size>131072:
        raise ValueError("checkpoint too large")
    snapshot=source.read_text(encoding="utf-8")
    if len(snapshot)>131072:
        raise ValueError("checkpoint too large")
    report=restore_from_corpus(snapshot,corpus_path,subject_gate,overlay)
    # Rebuild presentation cursor from accepted IDs only. Never replay content.
    seen={}
    for topic,ids in report.context.topics.items():
        hit=resolve_subject(corpus_path,topic)
        approved=set(ids)
        seen[topic]={p for p in hit.answer.split(" / ") if
                     proposition_id(topic,p.strip(),hit.provenance) in approved}
    topic_adapter.context.reset()
    proposition_cursor.reset()
    for topic in report.context.topics:
        topic_adapter.context.observe(topic)
    if report.context.active_topic in topic_adapter.context.topics:
        topic_adapter.context.observe(report.context.active_topic)
    proposition_cursor.seen.update(seen)
    return report
