"""Review-gated failure-driven repair queue. No automatic trust or model updates."""
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone

REJECTED={"REJECT_UNKNOWN","REJECT_NOT_ENTAILED","REJECT_UNGROUNDED","REJECT_LENGTH"}

class RepairQueue:
 def __init__(self,path):
  self.path=Path(path)
 def _load(self):
  if not self.path.exists():return []
  return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
 def _save(self,rows):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  temp=self.path.with_suffix(self.path.suffix+".tmp")
  temp.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
  temp.replace(self.path)
 def stage(self,question,candidate,evidence,gate):
  if gate not in REJECTED:raise ValueError("NOT_REJECTED")
  if evidence.get("status")!="EVIDENCE":raise ValueError("SOURCE_NOT_PRESENT")
  record={"id":str(uuid4()),"created_at":datetime.now(timezone.utc).isoformat(),
          "question":str(question),"rejected_candidate":str(candidate),
          "gate":gate,"evidence_url":str(evidence.get("url","")),
          "evidence_excerpt":str(evidence.get("excerpt","")),
          "answer_candidate":"","state":"PENDING_REPAIR","approval":"PENDING",
          "training_status":"NOT_READY"}
  rows=self._load();rows.append(record);self._save(rows)
  return record
 def list(self):return self._load()
 def propose(self,id,answer):
  answer=str(answer).strip()
  if not answer:raise ValueError("EMPTY_ANSWER")
  rows=self._load()
  for row in rows:
   if row["id"]==id:
    if row["state"] not in ("PENDING_REPAIR","PENDING_REVIEW"):raise ValueError("NOT_EDITABLE")
    row.update(answer_candidate=answer,state="PENDING_REVIEW",approval="PENDING")
    self._save(rows);return row
  raise KeyError(id)
 def approve(self,id):
  rows=self._load()
  for row in rows:
   if row["id"]==id:
    if row["state"]!="PENDING_REVIEW" or not row["answer_candidate"]:raise ValueError("NOT_READY_FOR_REVIEW")
    if not row["evidence_url"]:raise ValueError("SOURCE_URL_REQUIRED")
    row.update(state="APPROVED",approval="EXPLICIT_HUMAN",training_status="READY_FOR_EXPERIMENT")
    self._save(rows);return row
  raise KeyError(id)
 def reject(self,id):
  rows=self._load()
  for row in rows:
   if row["id"]==id:
    if row["state"]=="APPROVED":raise ValueError("APPROVED_IMMUTABLE")
    row.update(state="REJECTED",approval="REJECTED",training_status="NOT_READY")
    self._save(rows);return row
  raise KeyError(id)
 def export_approved(self,path):
  rows=[{"question":x["question"],"answer":x["answer_candidate"],
         "source_url":x["evidence_url"],"repair_id":x["id"]}
        for x in self._load() if x["state"]=="APPROVED"]
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
  path.write_text(json.dumps({"format":"llm-cha-repair-training-candidates-v1",
          "status":"EXPERIMENT_ONLY","pairs":rows},ensure_ascii=False,indent=2),encoding="utf-8")
  return len(rows)
