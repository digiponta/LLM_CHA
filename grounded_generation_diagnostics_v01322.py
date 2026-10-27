"""v0.13.22 append-only diagnostics for grounded unapproved generation.

Diagnostic records are local and never change approval or training state.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH=Path("results/grounded_generation_diagnostics_v01322.jsonl")

def make_record(question,evidence,generated,decision,model):
    return {
        "version":"v0.13.22",
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "question":str(question),
        "knowledge_id":evidence["knowledge_id"],
        "subject":evidence.get("subject",""),
        "source_text":evidence["source_text"],
        "source":evidence.get("source",""),
        "approval_state":"UNAPPROVED",
        "truth_state":"UNVERIFIED",
        "model":str(model),
        "raw_generation":generated.text,
        "generated_tokens":generated.token_count,
        "mean_confidence":generated.mean_confidence,
        "min_confidence":generated.min_confidence,
        "mean_top2_margin":generated.mean_top2_margin,
        "validation":decision["validation"],
        "route":decision["route"],
        "final_answer":decision["answer"],
        "accepted":decision["route"]=="GROUNDED_EXCERPT",
    }

def append_record(path,record):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as handle:
        handle.write(json.dumps(record,ensure_ascii=False)+"\n")
