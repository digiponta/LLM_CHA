"""Record evidence-gate rejection as a negative teacher signal, without training."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ALLOWED={"REJECT_UNKNOWN","REJECT_NOT_ENTAILED","REJECT_UNGROUNDED","REJECT_LENGTH"}

def make_negative_signal(question, rejected_answer, gate, evidence=None):
    q=" ".join(str(question or "").split())
    bad=" ".join(str(rejected_answer or "").split())
    if gate not in ALLOWED: raise ValueError("NOT_REJECTED")
    if not q or not bad: raise ValueError("EMPTY_NEGATIVE_SIGNAL")
    key=hashlib.sha256((q+"\n"+bad+"\n"+gate).encode("utf-8")).hexdigest()
    evidence=evidence or {}
    return {"id":key,"created_at":datetime.now(timezone.utc).isoformat(),
            "question":q,"rejected_answer":bad,"gate":gate,
            "evidence_topic":str(evidence.get("topic","")),
            "evidence_url":str(evidence.get("url","")),
            "signal":"NEGATIVE","weight":-1.0,
            "training_status":"NOT_TRAINED","positive_answer":None}

def append_negative_signal(path,question,rejected_answer,gate,evidence=None):
    row=make_negative_signal(question,rejected_answer,gate,evidence)
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():continue
            try: old=json.loads(raw)
            except json.JSONDecodeError:continue
            if old.get("id")==row["id"]:
                return {"status":"DUPLICATE","record":old}
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,ensure_ascii=False)+"\n")
    return {"status":"RECORDED","record":row}
