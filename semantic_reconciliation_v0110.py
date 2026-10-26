"""v0.11.0 experimental human-in-the-loop semantic reconciliation.

No semantic equivalence inference and no factual-truth promotion.
Callers must provide independently determined divergence status.
Writes use atomic replacement; an existing review is immutable.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile
import unicodedata
import uuid

VALID_DECISIONS = {"prefer_a", "prefer_b", "both_contextual", "neither"}
VALID_STATES = {"DIVERGENT", "EQUIVALENT", "UNKNOWN"}

def canonical_form(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip()

def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".reconcile-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

class ReconciliationStore:
    def __init__(self, store_dir="data/semantic_reconciliation_pending"):
        self.root = Path(store_dir)

    def _path(self, ticket_id):
        if not isinstance(ticket_id,str) or len(ticket_id)!=32 or any(c not in "0123456789abcdef" for c in ticket_id):
            raise ValueError("invalid ticket id")
        return self.root / (ticket_id + ".json")

    def open(self, question, answer_a, answer_b, *, evidence_a=None, evidence_b=None, divergence="DIVERGENT"):
        if divergence not in VALID_STATES:
            raise ValueError("invalid divergence state")
        if not all(isinstance(v,str) and v.strip() for v in (question,answer_a,answer_b)):
            raise ValueError("nonempty question and answers required")
        if canonical_form(answer_a)==canonical_form(answer_b):
            raise ValueError("equivalent surface strings: canonicalize instead of asking")
        if divergence=="EQUIVALENT":
            raise ValueError("do not request user adjudication for verified equivalence")
        record={"id":uuid.uuid4().hex,"version":"v0.11.0","state":"CLARIFICATION_PENDING",
                "divergence_status":divergence,"question":question,
                "candidates":{"a":{"text":answer_a,"evidence":evidence_a},
                              "b":{"text":answer_b,"evidence":evidence_b}},
                "review":None,"preferred_expression":None,
                "factual_truth":"UNVERIFIED","approval_state":"NOT_APPROVED",
                "created_at":datetime.now(timezone.utc).isoformat()}
        target=self._path(record["id"])
        _save(target,record)
        return record

    def get(self,ticket_id):
        return json.loads(self._path(ticket_id).read_text(encoding="utf-8"))

    def review(self,ticket_id,decision,*,context="",reviewer="user"):
        if decision not in VALID_DECISIONS:
            raise ValueError("invalid review decision")
        if not isinstance(context,str) or not isinstance(reviewer,str) or not reviewer.strip():
            raise ValueError("invalid context/reviewer")
        record=self.get(ticket_id)
        if record["state"]!="CLARIFICATION_PENDING":
            raise ValueError("ticket already reviewed: do not overwrite history")
        if decision=="both_contextual" and not context.strip():
            raise ValueError("both_contextual requires distinguishing context")
        expression=(record["candidates"]["a"]["text"] if decision=="prefer_a" else
                    record["candidates"]["b"]["text"] if decision=="prefer_b" else None)
        record["review"]={"decision":decision,"context":context,"reviewer":reviewer,
                          "at":datetime.now(timezone.utc).isoformat()}
        record["preferred_expression"]=expression
        record["state"]="USER_REVIEWED"
        # User preference does not prove factual truth or authorize /sleep training.
        _save(self._path(ticket_id),record)
        return record

def render_question(ticket):
    return ("候補の説明が一致しません。どちらを優先しますか？\\n"
            "質問: "+ticket["question"]+"\\n"
            "A: "+ticket["candidates"]["a"]["text"]+"\\n"
            "B: "+ticket["candidates"]["b"]["text"]+"\\n"
            "選択: prefer_a / prefer_b / both_contextual / neither")
