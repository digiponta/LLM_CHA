"""v0.6.40 explicit, validated persistence for topic evidence only."""
import json
import os
import tempfile
from pathlib import Path
from multi_topic_evidence_v0639 import TopicEvidenceContext

SCHEMA="llm-cha-topic-evidence-v0.6.40"
MAX_STRING=12000

def _validate(obj,max_topics):
    if not isinstance(obj,dict) or set(obj)!={"schema","active","topics"} or obj["schema"]!=SCHEMA:
        raise ValueError("unknown context schema")
    rows=obj["topics"]
    if not isinstance(rows,list) or len(rows)>max_topics:
        raise ValueError("invalid topic count")
    context=TopicEvidenceContext(max_topics=max_topics)
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"topic","extract","source","truth_state"}:
            raise ValueError("invalid topic record")
        if any(not isinstance(row[k],str) or len(row[k])>MAX_STRING for k in row):
            raise ValueError("invalid record text")
        if not row["topic"].strip() or row["truth_state"]!="EXTERNAL_UNVERIFIED":
            raise ValueError("invalid topic or truth state")
        if row["topic"] in context.items:
            raise ValueError("duplicate topic")
        context.remember(row["topic"],row["extract"],row["source"])
    active=obj["active"]
    if active is not None and (not isinstance(active,str) or active not in context.items):
        raise ValueError("invalid active topic")
    context.active=active
    return context

def export_context(context):
    data={"schema":SCHEMA,"active":context.active,"topics":list(context.items.values())}
    _validate(data,context.max_topics)
    return data

def save_context(context,path):
    dest=Path(path)
    data=export_context(context)
    dest.parent.mkdir(parents=True,exist_ok=True)
    # Same-directory atomic replacement prevents partially written files.
    name=None
    try:
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=dest.parent,
                                         prefix=".topic-",suffix=".tmp",delete=False) as out:
            name=out.name
            json.dump(data,out,ensure_ascii=False,indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(name,dest)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)
    return dest

def load_context(path,max_topics=4):
    source=Path(path)
    if source.stat().st_size>max_topics*(MAX_STRING*3+256)+1024:
        raise ValueError("context file too large")
    data=json.loads(source.read_text(encoding="utf-8-sig"))
    return _validate(data,max_topics)
